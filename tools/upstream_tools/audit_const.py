#!/usr/bin/env python3
"""Audit: hang so nao trong const.py thuc su duoc component dung."""
import re
from pathlib import Path

DIR = Path("/home/pi/.homeassistant/custom_components/vinfast")
const_src = (DIR / "const.py").read_text(encoding="utf-8")

# Ten hang so dinh nghia o cap module trong const.py
defined = set(re.findall(r'^([A-Z][A-Z0-9_]*)\s*=', const_src, re.M))
print("Hang so dinh nghia trong const.py:", len(defined))

uses: dict[str, set] = {}
for f in DIR.glob("*.py"):
    if f.name == "const.py":
        continue
    txt = f.read_text(encoding="utf-8", errors="replace")
    for name in defined:
        if re.search(rf'\b{name}\b', txt):
            uses.setdefault(name, set()).add(f.name)

print("\n=== DUOC DUNG (giu lai) ===")
for name in sorted(uses):
    print(f"  {name:34s} <- {', '.join(sorted(uses[name]))[:70]}")

print("\n=== KHONG DUOC DUNG (ung vien xoa) ===")
for name in sorted(defined - set(uses)):
    print(f"  {name}")
