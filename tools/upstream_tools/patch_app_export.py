#!/usr/bin/env python3
"""
Nang cap `app.py` (thu vien dung chung cua harvester):
  * `render_const()` dien them VIN + email vao khoi RENEWAL
  * `render_const()` dien device id theo tai khoan vao `device_id_by_email`
  * `write_const_files()` nhan them vin/email

Chay: python3 patch_app_export.py [--dry]
"""
from __future__ import annotations

import re
import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/app.py")
DRY = "--dry" in sys.argv

OLD_RENDER = '''def render_const(instance_id, timestamp, signature, device_id=None, template=None) -> str:
    """
    Điền giá trị UAA vào template ĐẦY ĐỦ (thay tại chỗ, thiếu dòng thì thêm vào cuối).
    """
    text = template if template is not None else load_const_template()
    fields = (
        ("UAA_CLIENT_INSTANCE_ID", instance_id),
        ("UAA_TIMESTAMP", timestamp),
        ("UAA_SIGNATURE", signature),
        ("DEVICE_ID", device_id),
    )
    for field, value in fields:
        if value is None or value == "":
            continue
        pattern = rf'({field}\\s*=\\s*")[^"]*(")'
        if re.search(pattern, text):
            text = re.sub(pattern, lambda m, v=value: f"{m.group(1)}{v}{m.group(2)}", text)
        else:
            text = text.rstrip("\\n") + f'\\n{field} = "{value}"\\n'
    return text
'''

NEW_RENDER = '''def render_const(instance_id, timestamp, signature, device_id=None, template=None,
                 vin=None, email=None) -> str:
    """
    Điền giá trị UAA vào template ĐẦY ĐỦ (thay tại chỗ, thiếu dòng thì thêm vào cuối).

    [2.9.58] Thêm ``vin`` và ``email``: hai giá trị này nằm TRONG khối ``RENEWAL``
    (khoá dict, không phải biến top-level) và là thông tin luồng gia hạn grant cần:
    thiếu ``vin`` thì ``telemetry/app/ping`` trả 403 dù token hợp lệ (đo 2026-10-10).
    """
    text = template if template is not None else load_const_template()
    fields = (
        ("UAA_CLIENT_INSTANCE_ID", instance_id),
        ("UAA_TIMESTAMP", timestamp),
        ("UAA_SIGNATURE", signature),
        ("DEVICE_ID", device_id),
    )
    for field, value in fields:
        if value is None or value == "":
            continue
        pattern = rf'({field}\\s*=\\s*")[^"]*(")'
        if re.search(pattern, text):
            text = re.sub(pattern, lambda m, v=value: f"{m.group(1)}{v}{m.group(2)}", text)
        else:
            text = text.rstrip("\\n") + f'\\n{field} = "{value}"\\n'

    # --- Khoá dict trong RENEWAL: "vin" và "email" ---
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

OLD_WRITE_SIG = "def write_const_files(instance_id, timestamp, signature, device_id=None) -> str:"
NEW_WRITE_SIG = ("def write_const_files(instance_id, timestamp, signature, device_id=None,\n"
                 "                      vin=None, email=None) -> str:")

OLD_WRITE_CALL = "    content = render_const(instance_id, timestamp, signature, device_id, template)"
NEW_WRITE_CALL = ("    content = render_const(instance_id, timestamp, signature, device_id, template,\n"
                  "                          vin=vin, email=email)")


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    orig = src

    for name, old, new in (("render_const", OLD_RENDER, NEW_RENDER),
                           ("write_const_files (chữ ký)", OLD_WRITE_SIG, NEW_WRITE_SIG),
                           ("write_const_files (gọi)", OLD_WRITE_CALL, NEW_WRITE_CALL)):
        if old not in src:
            print(f"  [BỎ QUA] {name}: không khớp (có thể đã vá)")
            continue
        src = src.replace(old, new, 1)
        print(f"  [OK]     {name}")

    if src == orig:
        print("Không có thay đổi.")
        return 0

    if DRY:
        print("--dry: không ghi gì.")
        return 0

    bak = APP.with_suffix(f".py.bak_export_{time.strftime('%Y%m%d_%H%M%S')}")
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
