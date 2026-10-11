#!/usr/bin/env python3
"""
Nang cap `vinfast_app.py` (harvester cong 5556):
  1. DEVICE_ID  -> 8feb7998824e390b (device id app 2.26.11 da dang ky)
  2. them `_resolve_vin(email)` tra VIN tu harvested_db.json roi vinfast_const.json
  3. truyen vin/email vao `core.write_const_files` khi xuat const.py + PEM

Chay: python3 patch_harvester_5556.py [--dry]
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/vinfast_app.py")
DRY = "--dry" in sys.argv

OLD_DEVICE = 'DEVICE_ID = "e0b6a4dedb5c8afe"'
NEW_DEVICE = 'DEVICE_ID = "8feb7998824e390b"  # [2.9.58] device id app 2.26.11'

OLD_CALL = "            path = core.write_const_files(iid, ts, sig, dev or None)"
NEW_CALL = ("            # [2.9.58] truyền VIN + email: thiếu VIN thì `telemetry/app/ping`\n"
            "            # trả 403 dù token hợp lệ, nên bản xuất phải mang theo VIN.\n"
            "            path = core.write_const_files(iid, ts, sig, dev or None,\n"
            "                                          vin=_resolve_vin(email),\n"
            "                                          email=email)")

HELPER = '''

def _resolve_vin(email) -> str:
    """[2.9.58] VIN của tài khoản — tra theo thứ tự, trả "" nếu chưa biết.

    1. `harvested_db.json[email]["vin"]`  (nếu bản harvest mới có lưu)
    2. `harvested_db.json[email]["vehicles"][0]["vinCode"]`
    3. `vinfast_const.json["accounts"][email]["vin"]`
    """
    if not email:
        return ""
    key = str(email).strip().lower()
    try:
        db = _db_load()
        rec = db.get(email) or db.get(key) or {}
        v = rec.get("vin")
        if v:
            return str(v).strip()
        for veh in (rec.get("vehicles") or []):
            if isinstance(veh, dict) and veh.get("vinCode"):
                return str(veh["vinCode"]).strip()
    except Exception:
        pass
    try:
        with open("/home/pi/vinfast/vinfast_const.json", encoding="utf-8") as f:
            c = json.load(f)
        acc = (c.get("accounts") or {}).get(key) or (c.get("accounts") or {}).get(email) or {}
        v = acc.get("vin")
        if v:
            return str(v).strip()
    except Exception:
        pass
    return ""

'''

ANCHOR = "def _db_load("


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    orig = src

    if OLD_DEVICE in src:
        src = src.replace(OLD_DEVICE, NEW_DEVICE, 1)
        print("  [OK] DEVICE_ID -> 8feb7998824e390b")
    elif NEW_DEVICE.split("  #")[0] in src:
        print("  [BỎ QUA] DEVICE_ID đã đúng")
    else:
        print("  [CẢNH BÁO] không tìm thấy dòng DEVICE_ID cũ")

    if OLD_CALL in src:
        src = src.replace(OLD_CALL, NEW_CALL, 1)
        print("  [OK] truyền vin/email vào write_const_files")
    elif "vin=_resolve_vin(email)" in src:
        print("  [BỎ QUA] write_const_files đã được vá")
    else:
        print("  [CẢNH BÁO] không tìm thấy lệnh gọi write_const_files")

    if "_resolve_vin" not in src:
        if ANCHOR in src:
            src = src.replace(ANCHOR, HELPER.lstrip("\n") + ANCHOR, 1)
            print("  [OK] thêm _resolve_vin()")
        else:
            print("  [CẢNH BÁO] không tìm thấy _db_load để chèn helper")
    else:
        print("  [BỎ QUA] _resolve_vin đã có")

    if src == orig:
        print("Không có thay đổi.")
        return 0
    if DRY:
        print("--dry: không ghi gì.")
        return 0

    bak = APP.with_suffix(f".py.bak_5556_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    print(f"Đã ghi {APP} (backup: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
        print("Biên dịch: OK")
    except py_compile.PyCompileError as exc:
        print("BIÊN DỊCH LỖI:", exc)
        shutil.copy2(bak, APP)
        print("Đã khôi phục bản cũ.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
