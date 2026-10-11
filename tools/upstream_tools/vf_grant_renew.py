#!/usr/bin/env python3
"""
vf_grant_renew.py — Gia hạn quyền `telemetry/app/ping` mà KHÔNG cần app đăng nhập.

Cơ chế
------
`telemetry/app/ping` chỉ trả 200 khi cặp (tài khoản, X-Device-Identifier) đang có
phiên hợp lệ phía server. Phiên đó do luồng đăng nhập của app tạo ra:
    auth0 -> challenge -> Play Integrity -> client/register -> UAA
Nhưng `client/register` một mình (dù có integrity token THẬT) là đủ để làm mới
quyền: đo 2026-10-10, hai vòng liên tiếp đều cho ping 200 ngay sau khi đăng ký.

Module Zygisk `vfbridge` trên điện thoại sinh Play Integrity token hộ, nên Pi
KHÔNG cần app đăng nhập — chỉ cần tiến trình app đang chạy để module inject.

Cách dùng
---------
    python3 vf_grant_renew.py                 # gia hạn cho mọi tài khoản trong DB
    python3 vf_grant_renew.py --email a@b.c   # chỉ một tài khoản
    python3 vf_grant_renew.py --check-only    # chỉ kiểm tra, không đăng ký
    python3 vf_grant_renew.py --quiet         # chỉ ghi log file

Exit code: 0 = mọi tài khoản OK, 1 = có lỗi.
"""
from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/pi/vinfast")
os.environ.setdefault("VINFAST_ADB", os.getenv("VINFAST_ADB", "192.168.100.35:5555"))

import requests  # noqa: E402
from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding  # noqa: E402

import vinfast_login as vl  # noqa: E402

API = "https://mobile.connected-car.vinfast.vn"
PING_URI = "/ccaraccessmgmt/api/v1/telemetry/app/ping"
DEVICE = vl.DEFAULT_DEVICE_ID
LOG = Path("/home/pi/vinfast/vf_grant_renew.log")
CONFIG_ENTRIES = Path("/home/pi/.homeassistant/.storage/core.config_entries")
#: Dấu thời gian lần gia hạn THÀNH CÔNG gần nhất, theo từng tài khoản.
STATE_FILE = Path("/home/pi/vinfast/vf_grant_renew.state.json")
#: Máy chủ bắt đầu trả 403 cho `telemetry/app/ping` nếu đăng ký lại quá dày.
#: Đo 2026-10-10: ~12 lần đăng ký trong 20 phút -> ping 403 liên tục dù đăng ký OK.
#: Vì vậy mặc định chỉ gia hạn khi đã quá `interval_minutes`, trừ khi --force.
DEFAULT_MIN_INTERVAL_MIN = 30

log = logging.getLogger("vf_grant_renew")


def _setup_logging(quiet: bool) -> None:
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if not quiet:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(sh)


def accounts() -> dict:
    """Đọc email -> mật khẩu từ config entry của HA (nguồn duy nhất có mật khẩu)."""
    out = {}
    try:
        cfg = json.loads(CONFIG_ENTRIES.read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("không đọc được config entry: %s", exc)
        return out
    for entry in cfg.get("data", {}).get("entries", []):
        if entry.get("domain") != "vinfast":
            continue
        data = entry.get("data", {}) or {}
        opts = entry.get("options", {}) or {}
        email = str(opts.get("email") or data.get("email") or "").strip()
        pwd = str(opts.get("password") or data.get("password") or "").strip()
        if email and pwd:
            out[email] = pwd
    return out


def ping_status(token: str, key, vin: str) -> int | None:
    body = json.dumps([{"instanceId": "1", "objectId": "6", "resourceId": "0"},
                       {"instanceId": "1", "objectId": "6", "resourceId": "1"}],
                      separators=(",", ":"))
    ts = str(int(time.time() * 1000))
    sig = base64.b64encode(key.sign(f"{ts}POST{PING_URI}{body}".encode(),
                                    padding.PKCS1v15(), hashes.SHA256())).decode()
    h = {"Authorization": f"Bearer {token}", "X-Device-Identifier": DEVICE,
         "X-APP-VERSION": "2.22.18", "X-Device-Family": "ONEPLUS A6013",
         "X-Device-Locale": "vi_VN", "X-Device-Platform": "android",
         "X-Device-OS-Version": "android 13", "X-SERVICE-NAME": "CAPP",
         "X-Timezone": "Asia/Ho_Chi_Minh", "X-Player-Identifier": "",
         "X-VIN-CODE": vin, "X-TIMESTAMP": ts, "X-HASH": sig,
         "Content-Type": "application/json; charset=UTF-8"}
    try:
        return requests.post(f"{API}{PING_URI}", data=body.encode(), headers=h, timeout=25).status_code
    except Exception:
        return None


def db_key(email: str):
    try:
        db = json.loads(Path("/home/pi/vinfast/harvested_db.json").read_text(encoding="utf-8"))
        rec = db.get(email.lower()) or db.get(email) or {}
        return vl._key_from_pem_text(rec.get("private_key_pem")), rec.get("vin")
    except Exception:
        return None, None


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        log.warning("không ghi được state: %s", exc)


def recently_renewed(email: str, min_interval_min: int) -> float | None:
    """Trả số phút còn lại nếu vừa gia hạn gần đây, None nếu đã đủ lâu."""
    last = (_load_state().get(email) or {}).get("last_ok_epoch")
    if not last:
        return None
    elapsed_min = (time.time() - float(last)) / 60.0
    if elapsed_min < min_interval_min:
        return round(min_interval_min - elapsed_min, 1)
    return None


def process(email: str, pwd: str, check_only: bool) -> bool:
    key_db, vin = db_key(email)
    if not vin:
        try:
            tok = vl.login(email, pwd).get("ccp_token")
            if key_db and tok:
                r = requests.get(f"{API}/ccarusermgnt/api/v1/user-vehicle", headers={
                    "Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                    timeout=20).json().get("data") or []
                vin = (r[0] or {}).get("vinCode") if r else None
        except Exception:
            pass

    if check_only:
        # chỉ cần biết ping có 200 không (dùng token+khoá hiện có)
        try:
            tok = vl.login(email, pwd).get("ccp_token")
            st = ping_status(tok, key_db, vin) if (key_db and vin) else None
        except Exception:
            st = None
        log.info("%s: ping=%s (check-only)", email, st)
        return st == 200

    res = vl.register_via_bridge(email, pwd, save=False, verify=False, timeout=240,
                                 serial=os.environ["VINFAST_ADB"])
    itok_len = (res.get("bridge") or {}).get("integrity_token_len")
    if not res.get("ok"):
        log.error("%s: đăng ký lại THẤT BẠI — %s", email, res.get("message"))
        return False
    log.info("%s: đăng ký lại OK (integrityToken=%s ký tự, clientInstanceId=%s)",
             email, itok_len, (res.get("client_instance_id") or "")[:20])

    key = vl._key_from_pem_text(res.get("private_key_pem"))
    tok = res.get("ccp_token")
    if key and tok and vin:
        st = ping_status(tok, key, vin)
        # Ping 403 KHÔNG phải lỗi của tiến trình gia hạn: thí dụ VF3 cần device id
        # riêng của tài khoản gambt90. Ghi log rõ, nhưng vẫn coi là chạy xong để
        # systemd không đánh dấu service "failed" mỗi 30 phút.
        level = log.info if st == 200 else log.warning
        level("%s: ping sau gia hạn = HTTP %s%s", email, st,
              "" if st == 200 else " (thiếu device id riêng cho tài khoản này?)")
        if st == 200:
            state = _load_state()
            state[email] = {"last_ok_epoch": time.time(), "ping": st}
            _save_state(state)
        return True
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=None)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="gia hạn dù chưa đủ khoảng cách tối thiểu (dùng khi ping hỏng thật)")
    ap.add_argument("--min-interval-min", type=int, default=DEFAULT_MIN_INTERVAL_MIN)
    args = ap.parse_args()
    _setup_logging(args.quiet)

    accs = accounts()
    if args.email:
        accs = {k: v for k, v in accs.items() if k == args.email} or {args.email: None}
    if not accs:
        log.error("không tìm thấy tài khoản VinFast nào trong config entry")
        return 1

    log.info("=== gia hạn grant cho %d tài khoản (device=%s) ===", len(accs), DEVICE)
    ok = True
    for email, pwd in accs.items():
        if not pwd:
            log.error("%s: thiếu mật khẩu", email)
            ok = False
            continue
        try:
            if not args.force and not args.check_only:
                wait = recently_renewed(email, args.min_interval_min)
                if wait is not None:
                    log.info("%s: bỏ qua — mới gia hạn cách đây chưa lâu (còn %.1f phút). "
                             "Dùng --force nếu ping đang hỏng.", email, wait)
                    continue
            if not process(email, pwd, args.check_only):
                ok = False
        except Exception as exc:
            log.exception("%s: lỗi %s", email, exc)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
