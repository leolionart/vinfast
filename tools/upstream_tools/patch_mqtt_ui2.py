#!/usr/bin/env python3
"""Vá chính xác khối host/port MQTT trong api_mqtt.py + bỏ dòng log trùng."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/.homeassistant/custom_components/vinfast/api_mqtt.py")

OLD_HEAD = '''            _rc = REGION_CONFIG.get(getattr(self.core, "region", "VN")) or REGION_CONFIG["VN"]
            _host = _rc.get("EMQX_HOST") or "ccp-mqtt.vinfast.vn"
            _port = int(_rc.get("EMQX_PORT") or 8884)
            _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- const.py: %s:%s (region=%s)",
                         _host, _port, getattr(self.core, "region", "VN"))
'''

NEW_HEAD = '''            # [2.9.60] host/port MQTT qua `emqx_server()` — ba tầng ưu tiên:
            #   1. người dùng nhập ở UI (Options: emqx_host / emqx_port)
            #   2. REGION_CONFIG trong const.py
            #   3. mặc định cứng (hành vi cũ)
            # Hai giá trị này KHÔNG endpoint nào trả về nên phải cấu hình được.
            _host, _port = emqx_server(getattr(self.core, "region", "VN"),
                                       getattr(self.core, "options", None))
            _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- %s:%s (region=%s)",
                         _host, _port, getattr(self.core, "region", "VN"))
'''

OLD_DUP = '''                # [2.9.59] host/port lấy từ const.py (REGION_CONFIG) — hai giá trị này
                # KHÔNG endpoint nào trả về, VinFast đổi máy chủ thì phải sửa const.py.
                # Fallback giữ nguyên giá trị cũ để const.py bản cũ vẫn chạy được.
                _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- const.py: %s:%s (region=%s)",
                             _host, _port, getattr(self.core, "region", "VN"))
                self.client.connect(_host, _port, 60)'''

NEW_DUP = '''                self.client.connect(_host, _port, 60)'''


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    changed = []
    if OLD_HEAD in src:
        src = src.replace(OLD_HEAD, NEW_HEAD, 1)
        changed.append("khối host/port -> emqx_server()")
    else:
        print("  [CẢNH BÁO] không khớp khối đầu")
    if OLD_DUP in src:
        src = src.replace(OLD_DUP, NEW_DUP, 1)
        changed.append("bỏ log trùng + comment cũ")
    else:
        print("  [CẢNH BÁO] không khớp khối log trùng")

    if not changed:
        print("Không có thay đổi.")
        return 1
    bak = APP.with_suffix(f".py.bak_ui2_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    print(f"Đã vá: {', '.join(changed)} (backup {bak.name}), biên dịch OK")

    # kiểm tra lại
    final = APP.read_text(encoding="utf-8")
    ok = (final.count("_rc = REGION_CONFIG.get") == 0
          and final.count("emqx_server(") >= 1
          and final.count("[CONST-SYNC] MQTT EMQX <-") == 1)
    print("Kiểm tra lại:", "SẠCH" if ok else "CÒN SÓT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
