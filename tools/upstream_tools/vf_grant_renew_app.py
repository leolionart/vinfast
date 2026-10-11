#!/usr/bin/env python3
"""
vf_grant_renew_app.py — Gia hạn grant bằng cách ĐĂNG NHẬP LẠI APP trên điện thoại.

ĐÍNH CHÍNH (2026-10-10)
-----------------------
Bản trước (`vf_grant_renew.py`, dùng bridge `client/register`) KHÔNG thực sự gia hạn.
Bảng đo đầy đủ cho thấy `telemetry/app/ping` chỉ trả 200 khi **app VinFast đã đăng nhập**
và grant còn hiệu lực; đăng ký qua bridge một mình không tạo được grant — thậm chí còn
đẩy app ra khỏi phiên và làm grant hết sớm hơn.

    app đăng nhập 15:48  -> ping 200 (15:49..16:07)
    bridge đăng ký 15:59 -> app bị đăng xuất
    ~16:12               -> ping 403 (grant hết hạn)
    app đăng nhập 16:30  -> ping 200 (18/18 bước PASS)

Vì vậy cách gia hạn ĐÚNG là điều khiển app đăng nhập lại qua adb — công thức đã chạy
thành công 4 lần trong phiên này.

Cách dùng
---------
    python3 vf_grant_renew_app.py --email thaitvad@gmail.com
    python3 vf_grant_renew_app.py --email thaitvad@gmail.com --check
Exit 0 = đã đăng nhập và ping 200 (hoặc --check thấy ping 200).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/pi/vinfast")

import requests  # noqa: E402
from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding  # noqa: E402

import vinfast_login as vl  # noqa: E402

PKG = "com.vinfast.companion.app"
ADBKB = "com.github.uiautomator/.AdbKeyboard"
GBOARD = "com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME"
API = "https://mobile.connected-car.vinfast.vn"
PING_URI = "/ccaraccessmgmt/api/v1/telemetry/app/ping"
HA_ENTRIES = Path("/home/pi/.homeassistant/.storage/core.config_entries")
DB_FILE = Path("/home/pi/vinfast/harvested_db.json")
CONST_FILE = Path("/home/pi/vinfast/vinfast_const.json")
DEVICE = vl.DEFAULT_DEVICE_ID
SERIAL = "192.168.100.35:5555"


def load_const() -> dict:
    """Const vận hành — nguồn VIN / device id / tham số cho luồng gia hạn.

    Bắt buộc: thiếu VIN trong const thì `telemetry/app/ping` trả 403 dù token hợp lệ
    (đo 2026-10-10: cùng token/khoá, có X-VIN-CODE -> 200, thiếu -> 403).
    """
    try:
        return json.loads(CONST_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"CẢNH BÁO: không đọc được {CONST_FILE}: {exc}")
        return {}


def const_for(email: str) -> dict:
    """(vin, device_id) hiệu lực cho một tài khoản, lấy từ const."""
    c = load_const()
    ren = c.get("renewal") or {}
    acc = (c.get("accounts") or {}).get(email) or {}
    mapped = {k.lower(): v for k, v in (ren.get("device_id_by_email") or {}).items()}
    return {
        "vin": acc.get("vin"),
        "iot_provider": acc.get("iot_provider"),
        "device_id": mapped.get(email.lower()) or ren.get("device_id_default") or DEVICE,
        "api_base": ren.get("api_base") or API,
    }

# Toạ độ màn hình 1080x2340 của OnePlus 6T
TAP_EMAIL = (539, 771)
TAP_PASS = (539, 1038)

log_lines: list[str] = []


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    log_lines.append(line)
    print(line, flush=True)


def adb(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["adb", "-s", SERIAL, *args], capture_output=True,
                          text=True, timeout=timeout)


def sh(cmd: str, timeout: int = 60) -> str:
    return adb("shell", cmd, timeout=timeout).stdout


def ensure_device() -> bool:
    out = adb("devices").stdout
    if SERIAL in out and "device" in out:
        return True
    adb("connect", SERIAL, timeout=30)
    time.sleep(3)
    out = adb("devices").stdout
    return SERIAL in out and "\tdevice" in out


def clear_proxy() -> None:
    # Xoá ĐỦ 5 khoá: chỉ xoá `http_proxy` sẽ để lại host/port legacy và app mất mạng.
    for k in ("http_proxy", "global_http_proxy_host", "global_http_proxy_port",
              "global_http_proxy_exclusion_list", "global_proxy_pac_url"):
        sh(f"settings delete global {k}")


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


def focused() -> str:
    return sh("dumpsys window | grep mCurrentFocus")


def logged_in() -> bool:
    return "NewMainActivity" in focused()


def app_login(email: str, pwd: str) -> bool:
    sh(f"ime set {ADBKB}")
    time.sleep(1)
    sh(f"am force-stop {PKG}")
    time.sleep(2)
    sh(f"monkey -p {PKG} -c android.intent.category.LAUNCHER 1")
    time.sleep(9)

    sh(f"input tap {TAP_EMAIL[0]} {TAP_EMAIL[1]}")
    time.sleep(2)
    sh("input keyevent KEYCODE_MOVE_END")
    for _ in range(45):
        sh("input keyevent KEYCODE_DEL")
    sh(f"input text '{email}'")
    time.sleep(2)

    sh(f"input tap {TAP_PASS[0]} {TAP_PASS[1]}")
    time.sleep(2)
    sh("input keyevent KEYCODE_MOVE_END")
    for _ in range(30):
        sh("input keyevent KEYCODE_DEL")
    # AdbKeyboard KHÔNG autocorrect -> `input text` giữ đúng chữ hoa.
    sh(f"input text '{pwd}'")
    time.sleep(2)
    sh("input keyevent 66")          # ENTER = IME action, đáng tin hơn tap nút
    time.sleep(15)
    ok = logged_in()
    if not ok:
        time.sleep(25)
        ok = logged_in()
    sh(f"ime set {GBOARD}")
    return ok


def ping_ok(email: str) -> tuple[bool, str]:
    cfgc = const_for(email)
    if not cfgc["vin"]:
        return False, "const thiếu VIN cho tài khoản này"
    db = json.loads(DB_FILE.read_text(encoding="utf-8"))
    rec = db.get(email.lower()) or db.get(email) or {}
    key = vl._key_from_pem_text(rec.get("private_key_pem"))
    if not key:
        return False, "không có khoá trong DB"
    try:
        tok = vl.login(email, ha_passwords()[email]).get("ccp_token")
    except Exception as exc:
        return False, f"login lỗi: {exc}"
    body = json.dumps([{"instanceId": "1", "objectId": "6", "resourceId": "0"},
                       {"instanceId": "1", "objectId": "6", "resourceId": "1"}],
                      separators=(",", ":"))
    ts = str(int(time.time() * 1000))
    sig = base64.b64encode(key.sign(f"{ts}POST{PING_URI}{body}".encode(),
                                    padding.PKCS1v15(), hashes.SHA256())).decode()
    h = {"Authorization": f"Bearer {tok}", "X-Device-Identifier": cfgc["device_id"],
         "X-APP-VERSION": "2.22.18", "X-Device-Family": "ONEPLUS A6013",
         "X-Device-Locale": "vi_VN", "X-Device-Platform": "android",
         "X-Device-OS-Version": "android 13", "X-SERVICE-NAME": "CAPP",
         "X-Timezone": "Asia/Ho_Chi_Minh", "X-Player-Identifier": email,
         "X-VIN-CODE": cfgc["vin"], "X-TIMESTAMP": ts, "X-HASH": sig,
         "Content-Type": "application/json; charset=UTF-8"}
    try:
        r = requests.post(f"{cfgc['api_base']}{PING_URI}", data=body.encode(),
                          headers=h, timeout=25)
        n = 0
        try:
            n = len(r.json().get("data") or [])
        except Exception:
            pass
        return r.status_code == 200, f"HTTP {r.status_code} ({n} key)"
    except Exception as exc:
        return False, f"lỗi mạng: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="thaitvad@gmail.com")
    ap.add_argument("--check", action="store_true", help="chỉ kiểm tra, không đăng nhập")
    args = ap.parse_args()
    email = args.email

    pwds = ha_passwords()
    if email not in pwds:
        log(f"LỖI: không có mật khẩu cho {email} trong config entry")
        return 1

    if not ensure_device():
        log(f"LỖI: không kết nối được adb tới {SERIAL}")
        return 1
    log(f"adb OK tới {SERIAL}")

    ok, detail = ping_ok(email)
    log(f"ping trước: {detail}")
    if ok or args.check:
        if args.check:
            return 0 if ok else 1
        log("grant còn hiệu lực, không cần đăng nhập lại")
        return 0

    clear_proxy()
    log("đã xoá proxy (đủ 5 khoá)")
    if app_login(email, pwds[email]):
        log("app đã đăng nhập (NewMainActivity)")
    else:
        log("CẢNH BÁO: app không vào được màn hình chính")
    time.sleep(8)
    ok, detail = ping_ok(email)
    log(f"ping sau: {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
