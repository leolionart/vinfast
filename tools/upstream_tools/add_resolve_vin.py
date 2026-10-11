#!/usr/bin/env python3
"""Chen ham `_resolve_vin()` vao vinfast_app.py (ngay truoc `def _db_load()`)."""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/vinfast_app.py")

HELPER = '''def _resolve_vin(email) -> str:
    """[2.9.58] VIN của tài khoản — tra theo thứ tự, trả "" nếu chưa biết.

    1. `harvested_db.json[email]["vin"]`
    2. `harvested_db.json[email]["vehicles"][0]["vinCode"]`
    3. `vinfast_const.json["accounts"][email]["vin"]`

    Vì sao cần: `telemetry/app/ping` trả 403 nếu request thiếu `X-VIN-CODE`, nên bản
    `const.py` xuất ra phải mang theo VIN của đúng tài khoản.
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

ANCHOR = "def _db_load()"


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if "def _resolve_vin" in src:
        print("Đã có _resolve_vin, không làm gì.")
        return 0
    if ANCHOR not in src:
        print("Không tìm thấy mỏ neo:", ANCHOR)
        return 1
    src = src.replace(ANCHOR, HELPER + ANCHOR, 1)
    bak = APP.with_suffix(f".py.bak_vin_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    print(f"Đã thêm _resolve_vin (backup {bak.name}), biên dịch OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
