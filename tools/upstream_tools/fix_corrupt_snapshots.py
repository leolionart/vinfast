#!/usr/bin/env python3
"""Sua 4 dong CONF_* trong cac const*.py da bi loi trung lap (chi o test_exports/)."""
import re
from pathlib import Path

FIX = {
    "CONF_UAA_CLIENT_INSTANCE_ID": "uaa_client_instance_id",
    "CONF_UAA_SIGNATURE": "uaa_signature",
    "CONF_UAA_TIMESTAMP": "uaa_timestamp",
    "CONF_VINFAST_PRIVATE_KEY": "vinfast_private_key",
}

fixed, skipped = [], []
for p in Path("/home/pi/vinfast").rglob("const*.py"):
    if not p.is_file():
        continue
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue
    m = re.search(r'^CONF_UAA_CLIENT_INSTANCE_ID\s*=\s*"([^"]*)"', txt, re.M)
    if not m or m.group(1) == "uaa_client_instance_id":
        continue
    orig = txt
    for key, want in FIX.items():
        txt = re.sub(rf'^{key}\s*=\s*"[^"]*"', f'{key} = "{want}"', txt, count=1, flags=re.M)
    if txt != orig:
        p.write_text(txt, encoding="utf-8")
        fixed.append(p)

print(f"Đã sửa {len(fixed)} file:")
for p in fixed:
    print("   ", p)

# Kiem tra lai
import importlib.util
bad = 0
for p in fixed:
    spec = importlib.util.spec_from_file_location("x", p)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
        assert m.CONF_UAA_CLIENT_INSTANCE_ID == "uaa_client_instance_id"
        assert m.UAA_CLIENT_INSTANCE_ID
    except Exception as exc:
        bad += 1
        print(f"   LỖI ở {p}: {exc}")
print(f"Kiểm tra lại: {len(fixed) - bad}/{len(fixed)} file hợp lệ")
