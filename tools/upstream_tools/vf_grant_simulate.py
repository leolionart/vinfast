#!/usr/bin/env python3
"""
vf_grant_simulate.py — Giả lập ĐẦY ĐỦ luồng gia hạn grant, có kiểm chứng
"lưu giữ không đổi" (không file nào bị ghi).

Mục đích
--------
Chạy y hệt luồng gia hạn thật, xác minh từng bước, nhưng:
  * KHÔNG lưu DB (`save=False`)
  * KHÔNG ghi đè khoá dùng chung (`apply_main=False`)
  * KHÔNG sửa config entry của HA
  * KHÔNG sửa const

Sau khi chạy xong, so SHA-256 của mọi file liên quan trước/sau; khác một byte là FAIL.

Cách dùng
---------
    /home/pi/vinfast/env/bin/python3 vf_grant_simulate.py
    /home/pi/vinfast/env/bin/python3 vf_grant_simulate.py --email thaitvad@gmail.com
    /home/pi/vinfast/env/bin/python3 vf_grant_simulate.py --no-register   # KHÔNG đăng ký
    /home/pi/vinfast/env/bin/python3 vf_grant_simulate.py --json

CẢNH BÁO — mỗi lần chạy ĐẦY ĐỦ tiêu tốn MỘT lần đăng ký thiết bị
-----------------------------------------------------------------
Đo 2026-10-10: sau ~12 lần đăng ký trong ~20 phút, endpoint `telemetry/app/ping`
bắt đầu trả 403 LIÊN TỤC — kể cả với token đang dùng tốt trước đó (HA cũng 403).
Vì vậy:
  * KHÔNG chạy giả lập đầy đủ liên tục để "thử cho chắc".
  * Muốn chỉ kiểm tra trạng thái grant, dùng `--no-register` (không tiêu tốn gì).
  * Gia hạn thật nên cách nhau ≥ 30 phút (`vf_grant_renew.py` đã tự chặn).

Exit code: 0 = mọi bước PASS và không file nào đổi; 1 = có bước FAIL.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/pi/vinfast")

CONST_FILE = Path("/home/pi/vinfast/vinfast_const.json")
DB_FILE = Path("/home/pi/vinfast/harvested_db.json")
HA_ENTRIES = Path("/home/pi/.homeassistant/.storage/core.config_entries")
SHARED_PEM = Path("/home/pi/vinfast/vinfast_private.pem")

#: Mọi file TUYỆT ĐỐI không được đổi trong suốt quá trình giả lập.
GUARDED = [CONST_FILE, DB_FILE, HA_ENTRIES, SHARED_PEM]

RESULTS: list[tuple[str, bool, str]] = []


def step(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(ok), detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return bool(ok)


def sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return "(không tồn tại)"
    except Exception as exc:
        return f"(lỗi {exc})"


def snapshot() -> dict:
    return {str(p): sha(p) for p in GUARDED}


def load_const() -> dict:
    return json.loads(CONST_FILE.read_text(encoding="utf-8"))


def ha_passwords() -> dict:
    cfg = json.loads(HA_ENTRIES.read_text(encoding="utf-8"))
    out = {}
    for e in cfg.get("data", {}).get("entries", []):
        if e.get("domain") != "vinfast":
            continue
        d, o = e.get("data", {}) or {}, e.get("options", {}) or {}
        email = str(o.get("email") or d.get("email") or "").strip()
        pwd = str(o.get("password") or d.get("password") or "").strip()
        if email and pwd:
            out[email] = pwd
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-register", action="store_true",
                    help="bỏ qua bước đăng ký (không tiêu tốn lượt), dùng bộ ba UAA đã lưu")
    args = ap.parse_args()

    os.environ.setdefault("VINFAST_ADB", "192.168.100.35:5555")
    import requests
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    import vinfast_login as vl
    import vf_bridge

    before = snapshot()
    print("=" * 88)
    print("GIẢ LẬP LUỒNG GIA HẠN GRANT VINFAST")
    print("=" * 88)
    print("File được bảo vệ (phải không đổi):")
    for p in GUARDED:
        print(f"   {p}  {before[str(p)][:16]}{'…' if len(before[str(p)]) > 16 else ''}")
    print()

    # ---------------------------------------------------------------- bước 1
    print("BƯỚC 1 — Đọc const vận hành")
    try:
        const = load_const()
        ren = const["renewal"]
        step("đọc vinfast_const.json", True, f"version={const.get('version')}")
        step("const có đủ khoá cho gia hạn",
             all(k in ren for k in ("enabled", "adb_target", "interval_minutes",
                                    "device_id_default", "device_id_by_email")),
             f"enabled={ren['enabled']} interval={ren['interval_minutes']}m")
        step("cấu hình gia hạn đang bật", bool(ren["enabled"]))
    except Exception as exc:
        step("đọc vinfast_const.json", False, f"{type(exc).__name__}: {exc}")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 2
    print("\nBƯỚC 2 — Chọn tài khoản & device id")
    accs = const.get("accounts", {})
    emails = [args.email] if args.email else list(accs.keys())
    emails = [e for e in emails if e]
    if not emails:
        step("có tài khoản trong const", False)
        return finish(before, args)
    email = emails[0]
    info = accs.get(email, {})
    vin_const = info.get("vin")
    device = (ren.get("device_id_by_email") or {}).get(email) or ren["device_id_default"]
    step("tài khoản có trong const", bool(info), email)
    step("có VIN trong const", bool(vin_const), str(vin_const))
    step("device id hiệu lực", bool(device) and len(device) >= 8, device)

    pwds = ha_passwords()
    step("có mật khẩu trong config entry HA", email in pwds,
         "đọc từ core.config_entries (chỉ đọc)")
    if email not in pwds:
        return finish(before, args)
    pwd = pwds[email]
    os.environ["VINFAST_ADB"] = ren["adb_target"]

    # ---------------------------------------------------------------- bước 3
    print("\nBƯỚC 3 — Bảo đảm bridge Play Integrity sẵn sàng trên điện thoại")
    try:
        st = vf_bridge.bridge_status(serial=ren["adb_target"])
        loaded = bool(st.get("vfbridge_loaded") and st.get("ready"))
        step("vfbridge đã nạp vào tiến trình app", loaded,
             f"app_pid={st.get('app_pid')} modules={len(st.get('zygisk_modules') or [])}")
        fdir = vf_bridge.ensure_bridge(timeout=180, serial=ren["adb_target"])
        step("ensure_bridge trả thư mục files", bool(fdir), str(fdir))
    except Exception as exc:
        step("bridge sẵn sàng", False, f"{type(exc).__name__}: {exc}")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 4
    print("\nBƯỚC 4 — Auth0 (bắt buộc có audience)")
    try:
        at = vl.auth0_login(email, pwd)["access_token"]
        step("Auth0 access_token", bool(at), f"{len(at)} ký tự")
    except Exception as exc:
        step("Auth0 login", False, f"{type(exc).__name__}: {exc}")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 5
    print("\nBƯỚC 5 — challenge")
    try:
        nonce = vl.get_challenge(at, device_id=device)
        ok = bool(nonce) and bool(re.match(r"^[0-9a-fA-F-]{8,64}$", str(nonce)))
        step("nonceRegister", ok, str(nonce))
    except Exception as exc:
        step("GET client/challenge", False, f"{type(exc).__name__}: {exc}")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 6
    if args.no_register:
        print("\nBƯỚC 6-10 — BỎ QUA (chế độ --no-register: không tiêu tốn lượt đăng ký)")
        db = json.loads(DB_FILE.read_text(encoding="utf-8"))
        rec = db.get(email.lower()) or db.get(email) or {}
        priv = vl._key_from_pem_text(rec.get("private_key_pem"))
        tok = vl.login(email, pwd).get("ccp_token")
        step("dùng khoá + bộ ba UAA đã lưu", bool(priv and tok),
             f"khoá={'có' if priv else 'KHÔNG'}, token={len(tok) if tok else 0} ký tự")
        step("khoá tạm KHÔNG ghi ra file",
             sha(SHARED_PEM) == before[str(SHARED_PEM)],
             "sha256 vinfast_private.pem giữ nguyên")
        if not (priv and tok):
            return finish(before, args)

        print("\nBƯỚC 11 — Xác minh quyền bằng API thật (không đăng ký)")
        h = vl._app_headers(tok, device)
        r = requests.get(f"{ren['api_base']}/ccarusermgnt/api/v1/user-vehicle",
                         headers=h, timeout=25)
        step("GET user-vehicle = 200", r.status_code == 200, f"HTTP {r.status_code}")
        veh = []
        try:
            veh = r.json().get("data") or []
        except Exception:
            pass
        got_vin = (veh[0] or {}).get("vinCode") if veh else None
        step("VIN trả về khớp const", got_vin == vin_const, f"{got_vin} (const: {vin_const})")

        print("\nBƯỚC 12 — telemetry/app/ping (không đăng ký)")
        body = json.dumps([{"instanceId": "1", "objectId": "6", "resourceId": "0"},
                           {"instanceId": "1", "objectId": "6", "resourceId": "1"},
                           {"instanceId": "1", "objectId": "34183", "resourceId": "9"}],
                          separators=(",", ":"))
        uri = "/ccaraccessmgmt/api/v1/telemetry/app/ping"
        t2 = str(int(time.time() * 1000))
        hh = dict(h)
        hh["Content-Type"] = "application/json; charset=UTF-8"
        hh["X-TIMESTAMP"] = t2
        hh["X-HASH"] = base64.b64encode(priv.sign(f"{t2}POST{uri}{body}".encode(),
                                                  padding.PKCS1v15(), hashes.SHA256())).decode()
        hh["X-VIN-CODE"] = vin_const or ""
        rp = requests.post(f"{ren['api_base']}{uri}", data=body.encode(), headers=hh, timeout=25)
        step("ping = 200", rp.status_code == 200, f"HTTP {rp.status_code}")
        try:
            keys = rp.json().get("data") or []
        except Exception:
            keys = []
        lat = next((i.get("value") for i in keys if i.get("deviceKey") == "00006_00001_00000"), None)
        lon = next((i.get("value") for i in keys if i.get("deviceKey") == "00006_00001_00001"), None)
        step("có toạ độ trong response ping", lat is not None and lon is not None,
             f"lat={lat} lon={lon} ({len(keys)} key)")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 6
    print("\nBƯỚC 6 — Khoá RSA tạm (KHÔNG lưu)")
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    os_pub = vf_bridge.os_public_key_spki(priv.public_key())
    step("sinh khoá RSA 2048 tạm", priv.key_size == 2048, "chỉ tồn tại trong RAM")
    step("osPublicKey SPKI base64", bool(os_pub) and len(os_pub) > 100,
         f"{len(os_pub)} ký tự")
    step("khoá tạm KHÔNG ghi ra file", not SHARED_PEM.exists() or sha(SHARED_PEM) == before[str(SHARED_PEM)],
         "sha256 vinfast_private.pem giữ nguyên")

    # ---------------------------------------------------------------- bước 7
    print("\nBƯỚC 7 — nonce cho Play Integrity")
    play_nonce = vf_bridge.play_integrity_nonce(nonce, os_pub)
    step("playNonce = sha256(nonceRegister + osPublicKey)",
         bool(re.match(r"^[0-9a-f]{64}$", play_nonce)), play_nonce[:32] + "…")

    # ---------------------------------------------------------------- bước 8
    print("\nBƯỚC 8 — Lấy Play Integrity token qua bridge")
    try:
        itok = vf_bridge.integrity_token(play_nonce, timeout=240, d=fdir,
                                         serial=ren["adb_target"])
        step("integrityToken thật", len(itok) > 100, f"{len(itok)} ký tự")
    except Exception as exc:
        step("integrity_token", False, f"{type(exc).__name__}: {exc}")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 9
    print("\nBƯỚC 9 — client/register")
    try:
        cid = vl.register_client(at, os_pub, nonce, itok, device_id=device)
        ok = bool(cid) and bool(re.match(r"^[0-9a-f-]{36}$", str(cid)))
        step("clientInstanceId", ok, str(cid))
    except Exception as exc:
        step("POST client/register", False, f"{type(exc).__name__}: {exc}")
        return finish(before, args)

    # ---------------------------------------------------------------- bước 10
    print("\nBƯỚC 10 — Chữ ký UAA + đổi token")
    ts = str(int(time.time() * 1000))
    sig = vl.sign_uaa(priv, cid, ts)
    step("sign_uaa sinh chữ ký", bool(sig) and len(sig) > 100, f"{len(sig)} ký tự")
    res = vl.uaa_exchange(priv, cid, ts, sig)
    step("CCP token", bool(res), f"{len(res) if res else 0} ký tự")
    if not res:
        return finish(before, args)
    tok = res

    # ---------------------------------------------------------------- bước 11
    print("\nBƯỚC 11 — Xác minh quyền bằng API thật")
    # LƯU Ý: `_app_headers` tự thêm tiền tố "Bearer " — chỉ truyền token trần,
    # truyền "Bearer xxx" sẽ thành "Bearer Bearer xxx" và bị 401.
    h = vl._app_headers(tok, device)
    r = requests.get(f"{ren['api_base']}/ccarusermgnt/api/v1/user-vehicle",
                     headers=h, timeout=25)
    veh = []
    try:
        veh = r.json().get("data") or []
    except Exception:
        pass
    step("GET user-vehicle = 200", r.status_code == 200, f"HTTP {r.status_code}")
    got_vin = (veh[0] or {}).get("vinCode") if veh else None
    step("VIN trả về khớp const", got_vin == vin_const, f"{got_vin} (const: {vin_const})")

    # ---------------------------------------------------------------- bước 12
    print("\nBƯỚC 12 — telemetry/app/ping")
    body = json.dumps([{"instanceId": "1", "objectId": "6", "resourceId": "0"},
                       {"instanceId": "1", "objectId": "6", "resourceId": "1"},
                       {"instanceId": "1", "objectId": "34183", "resourceId": "9"}],
                      separators=(",", ":"))
    uri = "/ccaraccessmgmt/api/v1/telemetry/app/ping"
    sig2 = base64.b64encode(priv.sign(f"{ts}POST{uri}{body}".encode(),
                                      padding.PKCS1v15(), hashes.SHA256())).decode()
    t2 = str(int(time.time() * 1000))
    hh = dict(h)
    # `_app_headers` không đặt Content-Type; POST kèm body mà thiếu nó -> HTTP 415.
    hh["Content-Type"] = "application/json; charset=UTF-8"
    hh["X-TIMESTAMP"] = t2
    hh["X-HASH"] = base64.b64encode(priv.sign(f"{t2}POST{uri}{body}".encode(),
                                              padding.PKCS1v15(), hashes.SHA256())).decode()
    hh["X-VIN-CODE"] = vin_const or ""
    # Máy chủ có lúc trả 403 tạm thời khi vừa đăng ký nhiều lần liên tiếp -> thử lại
    # vài lần trước khi kết luận, kèm in body để chẩn đoán.
    rp = None
    for attempt in range(1, 5):
        rp = requests.post(f"{ren['api_base']}{uri}", data=body.encode(),
                           headers=hh, timeout=25)
        if rp.status_code == 200:
            break
        body_txt = ""
        try:
            body_txt = rp.text[:160].replace("\n", " ")
        except Exception:
            pass
        print(f"        lần {attempt}: HTTP {rp.status_code} {body_txt}")
        if attempt < 4:
            time.sleep(12)
    if rp is not None:
        step("ping = 200", rp.status_code == 200, f"HTTP {rp.status_code}")
    keys = []
    try:
        keys = rp.json().get("data") or []
    except Exception:
        pass
    lat = next((i.get("value") for i in keys if i.get("deviceKey") == "00006_00001_00000"), None)
    lon = next((i.get("value") for i in keys if i.get("deviceKey") == "00006_00001_00001"), None)
    step("có toạ độ trong response ping", lat is not None and lon is not None,
         f"lat={lat} lon={lon}")
    step("X-Device-Identifier khớp const", hh["X-Device-Identifier"] == device, device)

    return finish(before, args)


def finish(before: dict, args) -> int:
    after = snapshot()
    print("\n" + "=" * 88)
    print("KIỂM CHỨNG 'LƯU GIỮ KHÔNG ĐỔI'")
    print("=" * 88)
    unchanged = True
    for p in GUARDED:
        same = before[str(p)] == after[str(p)]
        unchanged &= same
        print(f"   [{'OK  ' if same else 'ĐỔI '}] {p}")
    step("mọi file được bảo vệ KHÔNG đổi", unchanged,
         "không ghi DB, không ghi đè PEM, không sửa const/config entry")

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print("\n" + "=" * 88)
    print(f"KẾT QUẢ: {passed}/{total} bước PASS" + ("" if passed == total else "  ← CÓ BƯỚC FAIL"))
    print("=" * 88)

    if args.json:
        print(json.dumps({
            "passed": passed, "total": total,
            "steps": [{"name": n, "ok": ok, "detail": d} for n, ok, d in RESULTS],
            "files_unchanged": unchanged,
        }, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
