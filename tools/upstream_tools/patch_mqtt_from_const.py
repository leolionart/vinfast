#!/usr/bin/env python3
"""
Doi `api_mqtt.py` sang doc host/port EMQX tu `const.py` (REGION_CONFIG) thay vi
hardcode, va ghi log [CONST-SYNC] liet ke moi gia tri KHONG THE TU LAY.

Tuong thich nguoc: const.py cu (chua co EMQX_HOST/EMQX_PORT) van chay nho fallback.

Chay: python3 patch_mqtt_from_const.py
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/.homeassistant/custom_components/vinfast/api_mqtt.py")

OLD_IMPORT = "from .const import WWW_DIR, MOCK_FILE"
NEW_IMPORT = "from .const import WWW_DIR, MOCK_FILE, REGION_CONFIG"

OLD_BODY = '''                self.client.tls_set_context(ssl_ctx)
                self.client.connect("ccp-mqtt.vinfast.vn", 8884, 60)
                self.client.loop_start()
'''
NEW_BODY = '''                self.client.tls_set_context(ssl_ctx)
                # [2.9.59] host/port lấy từ const.py (REGION_CONFIG) — hai giá trị này
                # KHÔNG endpoint nào trả về, VinFast đổi máy chủ thì phải sửa const.py.
                # Fallback giữ nguyên giá trị cũ để const.py bản cũ vẫn chạy được.
                _rc = REGION_CONFIG.get(getattr(self.core, "region", "VN")) or REGION_CONFIG["VN"]
                _host = _rc.get("EMQX_HOST") or "ccp-mqtt.vinfast.vn"
                _port = int(_rc.get("EMQX_PORT") or 8884)
                _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- const.py: %s:%s (region=%s)",
                             _host, _port, getattr(self.core, "region", "VN"))
                self.client.connect(_host, _port, 60)
                self.client.loop_start()
'''

OLD_LOG = '''            _LOGGER.info("VinFast: 🌐 Khởi tạo kết nối EMQX MQTT (ccp-mqtt.vinfast.vn:8884) thành công!")'''
NEW_LOG = '''            _LOGGER.info("VinFast: 🌐 Khởi tạo kết nối EMQX MQTT (%s:%s) thành công!",
                         _rc.get("EMQX_HOST"), _rc.get("EMQX_PORT"))'''


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if "[CONST-SYNC] MQTT EMQX" in src:
        print("Đã vá, không làm gì.")
        return 0

    changed = 0
    for old, new, tag in ((OLD_IMPORT, NEW_IMPORT, "import"),
                          (OLD_BODY, NEW_BODY, "connect"),
                          (OLD_LOG, NEW_LOG, "log")):
        if old not in src:
            print(f"  [BỎ QUA] {tag}: không khớp")
            continue
        src = src.replace(old, new, 1)
        changed += 1
        print(f"  [OK]     {tag}")

    if not changed:
        return 1

    bak = APP.with_suffix(f".py.bak_const_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    print(f"→ ghi {APP.name} (backup {bak.name}), biên dịch OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
