#!/usr/bin/env python3
"""
Sua loi trung lap trong `render_const()` (app.py).

BENH
----
    pattern = rf'({field}\\s*=\\s*")[^"]*(")'
    text = re.sub(pattern, ..., text)          # KHONG co count=1

Voi `field = "UAA_CLIENT_INSTANCE_ID"`, mẫu này khớp CẢ HAI dòng:
    CONF_UAA_CLIENT_INSTANCE_ID = "uaa_client_instance_id"   <- tên khoá option
    UAA_CLIENT_INSTANCE_ID = ""                              <- giá trị UAA
nên `re.sub` ghi giá trị UAA **đè lên tên khoá option** -> `CONF_UAA_*` hỏng,
const.py xuất ra bị trùng lặp và component đọc sai khoá option.

THUỐC — hai lớp bảo vệ
    (?<![A-Za-z0-9_])   không cho ký tự định danh đứng ngay trước (loại `CONF_`)
    ^ ... re.M          chỉ khớp ở ĐẦU DÒNG (bản UAA legacy nằm ở cột 0)

Chay: python3 fix_render_dup.py [--dry]
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

APP = Path("/home/pi/vinfast/app.py")
DRY = "--dry" in sys.argv

OLD = r"""        pattern = rf'({field}\s*=\s*")[^"]*(")'
        if re.search(pattern, text):
            text = re.sub(pattern, lambda m, v=value: f"{m.group(1)}{v}{m.group(2)}", text)
        else:
            text = text.rstrip("\n") + f'\n{field} = "{value}"\n'"""

NEW = r'''        # (?<![A-Za-z0-9_]) loại `CONF_UAA_*` (tên khoá option) — nếu không,
        # re.sub sẽ ghi giá trị UAA đè lên tên khoá và làm hỏng `CONF_*`.
        # `^(?m)` chỉ khớp ở đầu dòng: bản UAA legacy nằm ở cột 0.
        pattern = rf'(?m)^(?<![A-Za-z0-9_])({field}\s*=\s*")[^"]*(")'
        if re.search(pattern, text):
            # count=1: chỉ thay dòng UAA thật, không đụng chỗ khác.
            text = re.sub(pattern, lambda m, v=value: f"{m.group(1)}{v}{m.group(2)}",
                          text, count=1)
        else:
            text = text.rstrip("\n") + f'\n{field} = "{value}"\n' '''.rstrip() + "\n"


def main() -> int:
    src = APP.read_text(encoding="utf-8")
    if "(?<![A-Za-z0-9_])" in src:
        print("Đã vá, không làm gì.")
        return 0
    if OLD not in src:
        print("Không khớp đoạn render_const cũ.")
        return 1
    src = src.replace(OLD, NEW, 1)
    if DRY:
        print("--dry: không ghi.")
        return 0
    bak = APP.with_suffix(f".py.bak_dup_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(APP, bak)
    APP.write_text(src, encoding="utf-8")
    import py_compile
    try:
        py_compile.compile(str(APP), doraise=True)
    except py_compile.PyCompileError as exc:
        print("LỖI BIÊN DỊCH:", exc)
        shutil.copy2(bak, APP)
        return 1
    print(f"Đã vá render_const (backup {bak.name}), biên dịch OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
