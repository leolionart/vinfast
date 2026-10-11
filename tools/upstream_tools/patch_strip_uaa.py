#!/usr/bin/env python3
"""
Nang cap `_strip_uaa()` trong app.py: ngoai UAA/DEVICE_ID con bo qua cac truong
DONG theo tai khoan trong khoi RENEWAL (vin, email, expected_ok, device_id_by_email)
de co `standard=True` khi const.py xuat ra dung chuan.

Chay: python3 patch_strip_uaa.py
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/vinfast_app.py")

OLD = '''def _strip_uaa(text: str) -> str:
    """Bỏ các dòng UAA để so sánh phần 'chuẩn' (template) giữa các bản const.py."""
    return "\\n".join(line for line in (text or "").splitlines()
                     if not any(k in line for k in _UAA_KEYS))
'''

NEW = '''#: Mẫu giá trị ĐỘNG theo từng tài khoản (khác nhau mỗi bản xuất) — quy về rỗng
#: trước khi đối chiếu "chuẩn", nếu không mọi bản xuất đều bị báo `standard=False`.
_DYNAMIC_PATTERNS = (
    (re.compile(r'("vin"\\s*:\\s*")[^"]*(")'), r"\\1\\2"),
    (re.compile(r'("email"\\s*:\\s*")[^"]*(")'), r"\\1\\2"),
    (re.compile(r'("expected_ok"\\s*:\\s*)\\[[^\\]]*\\]'), r"\\1[]"),
)
#: Dòng trong `device_id_by_email`: `"a@b.c": "deviceid",`
_DYNAMIC_EMAIL_MAP = re.compile(r'^\\s*"[^"]+@[^"]+"\\s*:\\s*"[^"]*",?\\s*$')


def _strip_uaa(text: str) -> str:
    """Bỏ giá trị ĐỘNG để so sánh phần 'chuẩn' (template) giữa các bản const.py.

    Động gồm: các dòng UAA (+ DEVICE_ID) và các trường theo tài khoản trong RENEWAL.
    """
    lines = []
    for line in (text or "").splitlines():
        if any(k in line for k in _UAA_KEYS):
            continue
        if _DYNAMIC_EMAIL_MAP.match(line):
            continue
        lines.append(line)
    out = "\\n".join(lines)
    for pattern, repl in _DYNAMIC_PATTERNS:
        out = pattern.sub(repl, out)
    return out
'''


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if "_DYNAMIC_PATTERNS" in src:
        print("Đã vá _strip_uaa, không làm gì.")
        return 0
    if OLD not in src:
        print("Không khớp _strip_uaa cũ.")
        return 1
    src = src.replace(OLD, NEW, 1)
    bak = APP.with_suffix(f".py.bak_strip_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    print(f"Đã vá _strip_uaa (backup {bak.name}), biên dịch OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
