#!/usr/bin/env python3
"""Cap nhat harvester theo const.py gon:
  * template = const.py moi (khong con RENEWAL)
  * render_const() dien tai khoan vao DEVICE_ID_BY_EMAIL (HA DUNG) thay vi RENEWAL.vin/email
  * bo qua cac dong dong trong DEVICE_ID_BY_EMAIL khi doi chieu "chuan"

Chay: python3 patch_const_gon.py
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/app.py")
VAPP = Path("/home/pi/vinfast/vinfast_app.py")

# --- 1. app.py: render_const + write_const_files ---
OLD_RENDER_BLOCK = '''    # --- Khoá dict trong RENEWAL: "vin" và "email" ---
    for key, value in (("vin", vin), ("email", email)):
        if not value:
            continue
        pattern = rf'("{key}"\\s*:\\s*")[^"]*(")'
        if re.search(pattern, text):
            text = re.sub(pattern, lambda m, v=value: f"{m.group(1)}{v}{m.group(2)}",
                          text, count=1)
        else:
            log_ui(f"Template thiếu khoá RENEWAL['{key}'] -> bỏ qua.", "WARNING")

    # --- Ghi device id của tài khoản vào bảng theo-email để HA dùng đúng ---
    if device_id and email:
        pattern = r'("device_id_by_email"\\s*:\\s*\\{)'
        if re.search(pattern, text):
            entry = f'"{email}": "{device_id}", '
            if f'"{email}"' not in text:
                text = re.sub(pattern, lambda m: m.group(1) + "\\n        " + entry,
                              text, count=1)
    return text
'''

NEW_RENDER_BLOCK = '''    # --- Ghi tài khoản vào DEVICE_ID_BY_EMAIL: đây là dòng HA THỰC SỰ DÙNG
    # --- (`device_id_for()` trong const.py đọc bảng này để chọn X-Device-Identifier).
    if device_id and email and f'"{email}"' not in text:
        pattern = r'(DEVICE_ID_BY_EMAIL\\s*=\\s*\\{)'
        if re.search(pattern, text):
            text = re.sub(pattern,
                          lambda m: m.group(1) + f'\\n    "{email}": "{device_id}",',
                          text, count=1)
        else:
            log_ui("Template thiếu DEVICE_ID_BY_EMAIL -> bỏ qua.", "WARNING")
    return text
'''

# --- 2. vinfast_app.py: _strip_uaa bo qua dong dong trong DEVICE_ID_BY_EMAIL ---
OLD_DYN = '''_DYNAMIC_EMAIL_MAP = re.compile(r'^\\s*"[^"]+@[^"]+"\\s*:\\s*"[^"]*",?\\s*$')
'''
NEW_DYN = '''#: Dòng trong `DEVICE_ID_BY_EMAIL` (sinh theo tài khoản) — bỏ khi đối chiếu "chuẩn".
_DYNAMIC_EMAIL_MAP = re.compile(r'^\\s*"[^"]+@[^"]+"\\s*:\\s*"[^"]*",?\\s*$')
_PLACEHOLDERS = (re.compile(r'^\\s*"vin"\\s*:\\s*"[^"]*",?\\s*$'),
                 re.compile(r'^\\s*"email"\\s*:\\s*"[^"]*",?\\s*$'),
                 re.compile(r'^\\s*"expected_ok"\\s*:\\s*\\[[^\\]]*\\],?\\s*$'))
'''
OLD_LOOP = '''        if _DYNAMIC_EMAIL_MAP.match(line):
            continue
'''
NEW_LOOP = '''        if _DYNAMIC_EMAIL_MAP.match(line):
            continue
        if any(p.match(line) for p in _PLACEHOLDERS):
            continue
'''


def patch(path: Path, pairs, label: str) -> bool:
    src = path.read_text(encoding="utf-8")
    changed = False
    for old, new, tag in pairs:
        if old not in src:
            print(f"  [BỎ QUA] {label}/{tag}: không khớp")
            continue
        src = src.replace(old, new, 1)
        changed = True
        print(f"  [OK]     {label}/{tag}")
    if not changed:
        return False
    bak = path.with_suffix(f".py.bak_gon_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(path, bak)
    path.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        print("  LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, path)
        return False
    print(f"  → ghi {path.name} (backup {bak.name})")
    return True


def main() -> int:
    patch(APP, [(OLD_RENDER_BLOCK, NEW_RENDER_BLOCK, "render_const")], "app.py")
    patch(VAPP, [(OLD_DYN, NEW_DYN, "hằng số"),
                 (OLD_LOOP, NEW_LOOP, "vòng lọc")], "vinfast_app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
