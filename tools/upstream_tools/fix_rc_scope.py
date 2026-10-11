#!/usr/bin/env python3
"""Sua loi `_rc` khong ton tai ngoai pham vi `_setup_emqx()` trong api_mqtt.py."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/.homeassistant/custom_components/vinfast/api_mqtt.py")

OLD = '''            def _setup_emqx():
                ssl_ctx = ssl.create_default_context()'''
NEW = '''            # [2.9.59] host/port lấy từ const.py (REGION_CONFIG) — hai giá trị này
            # KHÔNG endpoint nào trả về, VinFast đổi máy chủ thì phải sửa const.py.
            # Fallback giữ nguyên giá trị cũ để const.py bản cũ vẫn chạy được.
            # Tính Ở ĐÂY (không phải trong `_setup_emqx`) để dòng log cuối hàm dùng được.
            _rc = REGION_CONFIG.get(getattr(self.core, "region", "VN")) or REGION_CONFIG["VN"]
            _host = _rc.get("EMQX_HOST") or "ccp-mqtt.vinfast.vn"
            _port = int(_rc.get("EMQX_PORT") or 8884)

            def _setup_emqx():
                ssl_ctx = ssl.create_default_context()'''

OLD_INNER = '''                # [2.9.59] host/port lấy từ const.py (REGION_CONFIG) — hai giá trị này
                # KHÔNG endpoint nào trả về, VinFast đổi máy chủ thì phải sửa const.py.
                # Fallback giữ nguyên giá trị cũ để const.py bản cũ vẫn chạy được.
                _rc = REGION_CONFIG.get(getattr(self.core, "region", "VN")) or REGION_CONFIG["VN"]
                _host = _rc.get("EMQX_HOST") or "ccp-mqtt.vinfast.vn"
                _port = int(_rc.get("EMQX_PORT") or 8884)
                _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- const.py: %s:%s (region=%s)",
                             _host, _port, getattr(self.core, "region", "VN"))
                self.client.connect(_host, _port, 60)'''
NEW_INNER = '''                _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- const.py: %s:%s (region=%s)",
                             _host, _port, getattr(self.core, "region", "VN"))
                self.client.connect(_host, _port, 60)'''


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if src.count("_rc = REGION_CONFIG.get") == 1:
        print("Đã đúng (chỉ 1 chỗ tính _rc), không làm gì.")
        return 0
    changed = False
    if OLD_INNER in src:
        src = src.replace(OLD_INNER, NEW_INNER, 1)
        changed = True
        print("  [OK] bỏ khối tính _rc trong _setup_emqx")
    if OLD in src:
        src = src.replace(OLD, NEW, 1)
        changed = True
        print("  [OK] thêm khối tính _rc trước _setup_emqx")
    if not changed:
        print("Không khớp mẫu nào.")
        return 1

    bak = APP.with_suffix(f".py.bak_rc_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
        print(f"→ ghi {APP.name} (backup {bak.name}), biên dịch OK")
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
