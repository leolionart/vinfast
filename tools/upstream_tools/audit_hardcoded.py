#!/usr/bin/env python3
"""
Liet ke moi gia tri 'khong the tu lay' trong component: host/port/URL/domain hardcode
(khong den tu API, khong den tu config entry, khong den tu const.py).
"""
import re
from pathlib import Path

DIR = Path("/home/pi/.homeassistant/custom_components/vinfast")
SKIP = {"const.py", "const_common.py"}

PATTERNS = [
    ("host/domain", re.compile(r'["\']([a-z0-9][a-z0-9\-\.]*\.(?:vn|com|net|io))(?::(\d+))?["\']')),
    ("url", re.compile(r'["\'](https?://[^"\']+)["\']')),
    ("port", re.compile(r'\bconnect\(\s*["\']([^"\']+)["\']\s*,\s*(\d+)')),
    ("ip", re.compile(r'["\'](\d{1,3}(?:\.\d{1,3}){3})(?::(\d+))?["\']')),
]

found: dict[str, set] = {}
for f in sorted(DIR.glob("*.py")):
    if f.name in SKIP:
        continue
    txt = f.read_text(encoding="utf-8", errors="replace")
    for kind, pat in PATTERNS:
        for m in pat.finditer(txt):
            val = m.group(0).strip("\"'")
            line_no = txt[:m.start()].count("\n") + 1
            found.setdefault(kind, set()).add(f"{val}   [{f.name}:{line_no}]")

for kind in ("port", "host/domain", "ip", "url"):
    rows = sorted(found.get(kind, ()))
    if not rows:
        continue
    print(f"\n=== {kind} ({len(rows)}) ===")
    for r in rows:
        print("  ", r)
