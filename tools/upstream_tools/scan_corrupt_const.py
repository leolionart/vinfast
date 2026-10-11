#!/usr/bin/env python3
"""Quet moi const*.py xem file nao bi loi trung lap (CONF_UAA_* chua gia tri UAA)."""
import re
from pathlib import Path

ROOTS = [Path("/home/pi/vinfast"), Path("/home/pi/.homeassistant/custom_components/vinfast")]
PAT = re.compile(r'^CONF_UAA_CLIENT_INSTANCE_ID\s*=\s*"([^"]*)"', re.M)

bad, good, total = [], 0, 0
for root in ROOTS:
    for p in root.rglob("const*.py"):
        if not p.is_file():
            continue
        total += 1
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = PAT.search(txt)
        if not m:
            continue
        val = m.group(1)
        if val != "uaa_client_instance_id":
            bad.append((str(p), val[:40]))

print(f"Đã quét {total} file const*.py")
print(f"File BỊ LỖI (CONF_UAA_CLIENT_INSTANCE_ID chứa giá trị UAA): {len(bad)}\n")
for path, val in bad:
    print(f"   {path}\n      -> {val}…")

if not bad:
    print("   (không có file nào bị lỗi)")

print("\n=== 3 bản const.py đang dùng ===")
import hashlib
for f in ("/home/pi/.homeassistant/custom_components/vinfast/const.py",
          "/home/pi/vinfast/const.py",
          "/home/pi/vinfast/const_template.py"):
    p = Path(f)
    if p.exists():
        print(f"   {hashlib.sha256(p.read_bytes()).hexdigest()[:16]}  {p.stat().st_size:5d}  {f}")
