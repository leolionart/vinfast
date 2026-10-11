#!/usr/bin/env python3
"""
Nang cap `vinfast_login.py`: `register_via_bridge()` luu them VIN (va danh sach xe)
vao `harvested_db.json`.

Vi sao: DB hien KHONG luu VIN, nen buoc xuat `const.py` phai tra VIN tu nguon khac;
thieu VIN thi `telemetry/app/ping` tra 403 du token hop le (do 2026-10-10). Luu VIN
ngay tai luc dang ky lam moi thu sau do (export const/pem, gia hạn, ping) tu du.

Chay: python3 patch_login_save_vin.py
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/vinfast_login.py")

OLD = '''        out["saved"] = _save_db_entry(email, {
            "password": password,
            "uaa_client_instance_id": cid,
            "uaa_timestamp": ts,
            "uaa_signature": sig,
            "private_key_pem": pem_text,
            "device_id": DEFAULT_DEVICE_ID,
        }, db_path=db_path)'''

NEW = '''        # [2.9.58] Lưu kèm VIN + danh sách xe. DB trước đây KHÔNG có VIN, nên bước
        # xuất const.py phải đi tra nơi khác; thiếu VIN thì `telemetry/app/ping`
        # trả 403 dù token hợp lệ. Lưu ngay ở đây để về sau tự đủ.
        entry = {
            "password": password,
            "uaa_client_instance_id": cid,
            "uaa_timestamp": ts,
            "uaa_signature": sig,
            "private_key_pem": pem_text,
            "device_id": DEFAULT_DEVICE_ID,
        }
        vehicles = out.get("vehicles") or []
        if vehicles:
            entry["vehicles"] = vehicles
            first = vehicles[0] if isinstance(vehicles[0], dict) else {}
            vin_code = first.get("vinCode") or first.get("vin")
            if vin_code:
                entry["vin"] = vin_code
        out["saved"] = _save_db_entry(email, entry, db_path=db_path)'''


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if '"vehicles": vehicles' in src:
        print("Đã vá, không làm gì.")
        return 0
    if OLD not in src:
        print("Không khớp đoạn _save_db_entry trong register_via_bridge.")
        return 1
    bak = APP.with_suffix(f".py.bak_vin_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    print(f"Đã lưu VIN vào DB khi đăng ký (backup {bak.name}), biên dịch OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
