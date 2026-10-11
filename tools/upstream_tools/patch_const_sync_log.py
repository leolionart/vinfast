#!/usr/bin/env python3
"""
Them log [CONST-SYNC] vao __init__.py: liet ke moi gia tri HA KHONG THE TU LAY
va nguon cua no, ngay khi setup config entry. Lech const.py <-> HA hien ra trong log.
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/.homeassistant/custom_components/vinfast/__init__.py")

ANCHOR = """    api = VinFastAPI(email, password, region=region, lang=lang, gemini_api_key=gemini_key, options=entry.options)
    api.hass = hass
    api.data = new_data
"""

NEW = '''    api = VinFastAPI(email, password, region=region, lang=lang, gemini_api_key=gemini_key, options=entry.options)
    api.hass = hass
    api.data = new_data

    # [2.9.59] [CONST-SYNC] In ra mọi giá trị HA KHÔNG THỂ TỰ LẤY, kèm nguồn.
    # Mục đích: khi const.py lệch với config entry / harvested_db thì thấy ngay trong
    # log thay vì đoán qua triệu chứng (sai device id -> ping 403 y như "xe đang ngủ").
    try:
        _rc = REGION_CONFIG.get(region) or REGION_CONFIG["VN"]
        _dev = api._device_id() if hasattr(api, "_device_id") else DEVICE_ID
        _opt_dev = str(entry.options.get("device_id") or entry.data.get("device_id") or "")
        _uaa = str(entry.options.get("uaa_client_instance_id")
                   or entry.data.get("uaa_client_instance_id") or "")
        _db_uaa = ""
        try:
            import json as _json
            with open("/home/pi/vinfast/harvested_db.json", encoding="utf-8") as _f:
                _db_uaa = str((_json.load(_f).get(str(email or "").lower()) or {})
                              .get("uaa_client_instance_id") or "")
        except Exception:
            pass
        _LOGGER.info(
            "VinFast: [CONST-SYNC] region=%s | API=%s | IOT=%s | EMQX=%s:%s | "
            "device_id=%s (const=%s, option=%s) | UAA=%s (entry=%s, db=%s)",
            region, _rc.get("API_BASE"), _rc.get("IOT_ENDPOINT"),
            _rc.get("EMQX_HOST"), _rc.get("EMQX_PORT"),
            _dev, (DEVICE_ID_BY_EMAIL or {}).get(str(email or "").lower(), DEVICE_ID),
            _opt_dev or "(không đặt)",
            (_uaa[:8] + "…") if _uaa else "(rỗng)",
            "khớp" if (_uaa and _db_uaa and _uaa == _db_uaa) else
            ("chỉ có ở entry" if _uaa and not _db_uaa else
             ("chỉ có ở db" if _db_uaa and not _uaa else
              ("KHỚP" if not _uaa and not _db_uaa else "LỆCH"))),
            (_db_uaa[:8] + "…") if _db_uaa else "(rỗng)",
        )
    except Exception as _exc:  # noqa: BLE001 — log không được làm hỏng setup
        _LOGGER.debug("VinFast: [CONST-SYNC] không dựng được dòng log: %s", _exc)
'''

OLD_IMPORT = ("from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, "
              "CONF_GEMINI_API_KEY, CONF_REGION, CONF_LANGUAGE")
NEW_IMPORT = ("from .const import (DOMAIN, CONF_EMAIL, CONF_PASSWORD,\n"
              "                    CONF_GEMINI_API_KEY, CONF_REGION, CONF_LANGUAGE,\n"
              "                    REGION_CONFIG, DEVICE_ID, DEVICE_ID_BY_EMAIL)")


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if "[CONST-SYNC] region=" in src:
        print("Đã vá, không làm gì.")
        return 0
    if ANCHOR not in src:
        print("Không tìm thấy mỏ neo trong __init__.py")
        return 1
    if OLD_IMPORT in src:
        src = src.replace(OLD_IMPORT, NEW_IMPORT, 1)
        print("  [OK]     import REGION_CONFIG/DEVICE_ID/DEVICE_ID_BY_EMAIL")
    else:
        print("  [CẢNH BÁO] không khớp dòng import — kiểm tra tay")
    src = src.replace(ANCHOR, NEW, 1)
    bak = APP.with_suffix(f".py.bak_sync_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
        print(f"Đã thêm log [CONST-SYNC] (backup {bak.name}), biên dịch OK")
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
