#!/usr/bin/env python3
"""So sanh const.py MOI voi cac ban CU de liet ke chinh xac phan bo sung."""
import difflib
import importlib.util
import sys
from pathlib import Path

NEW = Path("/home/pi/.homeassistant/custom_components/vinfast/const.py")
OLDS = {
    "const.py GỐC của component (trước khi tôi sửa)":
        Path("/home/pi/.homeassistant/custom_components/vinfast/const.py.bak_deviceid"),
    "const_template.py GỐC của bộ harvest":
        next(Path("/home/pi/vinfast").glob("const_uaa_09h41m54s.py"), None),
    "const.py trước khi gọn (còn RENEWAL)":
        Path("/home/pi/.homeassistant/custom_components/vinfast/const.py.bak_gon_20261010_165209"),
}

new_lines = NEW.read_text(encoding="utf-8").splitlines()
print(f"const.py MỚI: {len(new_lines)} dòng, {NEW.stat().st_size} byte\n")

for label, old in OLDS.items():
    if old is None or not old.exists():
        print(f"### {label}: KHÔNG TÌM THẤY\n")
        continue
    old_lines = old.read_text(encoding="utf-8").splitlines()
    print("=" * 88)
    print(f"### {label}")
    print(f"    {old.name}: {len(old_lines)} dòng, {old.stat().st_size} byte")
    print("=" * 88)
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm="",
                                     fromfile="CŨ", tofile="MỚI", n=1))
    added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]
    print(f"  + {len(added)} dòng thêm | - {len(removed)} dòng bỏ\n")
    print("  --- THÊM ---")
    for l in added:
        print("   +", l if l.strip() else "(dòng trống)")
    if removed:
        print("\n  --- BỎ ---")
        for l in removed:
            print("   -", l if l.strip() else "(dòng trống)")
    print()
