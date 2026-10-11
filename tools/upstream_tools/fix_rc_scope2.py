#!/usr/bin/env python3
"""Chuyen khoi tinh `_rc`/`_host`/`_port` ra TRUOC `def _setup_emqx()` trong api_mqtt.py."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/.homeassistant/custom_components/vinfast/api_mqtt.py")

BLOCK = [
    "                _rc = REGION_CONFIG.get(getattr(self.core, \"region\", \"VN\")) or REGION_CONFIG[\"VN\"]\n",
    "                _host = _rc.get(\"EMQX_HOST\") or \"ccp-mqtt.vinfast.vn\"\n",
    "                _port = int(_rc.get(\"EMQX_PORT\") or 8884)\n",
]
ANCHOR = "            def _setup_emqx():\n"
INDENTED = [
    "            _rc = REGION_CONFIG.get(getattr(self.core, \"region\", \"VN\")) or REGION_CONFIG[\"VN\"]\n",
    "            _host = _rc.get(\"EMQX_HOST\") or \"ccp-mqtt.vinfast.vn\"\n",
    "            _port = int(_rc.get(\"EMQX_PORT\") or 8884)\n",
    "            _LOGGER.info(\"VinFast: [CONST-SYNC] MQTT EMQX <- const.py: %s:%s (region=%s)\",\n",
    "                         _host, _port, getattr(self.core, \"region\", \"VN\"))\n",
]


def main() -> int:
    lines = APP.read_text(encoding="utf-8").splitlines(keepends=True)

    # 1. Bo 3 dong dinh nghia ben trong _setup_emqx
    removed = 0
    out = []
    for ln in lines:
        if ln in BLOCK:
            removed += 1
            continue
        out.append(ln)
    if removed != 3:
        print(f"  CẢNH BÁO: bỏ được {removed}/3 dòng (kiểm tra tay)")
    lines = out

    # 2. Chen khoi dung pham vi truoc `def _setup_emqx()`
    idx = next((i for i, ln in enumerate(lines) if ln == ANCHOR), None)
    if idx is None:
        print("  Không tìm thấy mốc 'def _setup_emqx()'")
        return 1
    lines[idx:idx] = INDENTED
    print("  [OK] đã chuyển khối tính _rc ra trước _setup_emqx")

    bak = APP.with_suffix(f".py.bak_scope_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text("".join(lines), encoding="utf-8")
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
