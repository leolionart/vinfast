#!/usr/bin/env python3
"""Kiem chung nang cap harvester 5556 sau khi restart."""
import importlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, "/home/pi/vinfast")

print("=== 1. Service 5556 ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:5556/", timeout=20) as r:
        print("   HTTP", r.status)
except Exception as e:
    print("   LỖI:", e)

print("\n=== 2. _resolve_vin ===")
import vinfast_app as va
for e in ("thaitvad@gmail.com", "gambt90@gmail.com", "nobody@x.yz", None):
    print(f"   {str(e):26s} -> {va._resolve_vin(e)!r}")

print("\n=== 3. DEVICE_ID cua harvester ===")
print("   DEVICE_ID =", va.DEVICE_ID)

print("\n=== 4. Export const.py + PEM ===")
req = urllib.request.Request(
    "http://127.0.0.1:5556/export_const",
    data=json.dumps({"email": "thaitvad@gmail.com"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=120) as r:
    body = json.loads(r.read().decode())
print("   status:", body.get("status"))
for label, info in (body.get("written") or {}).items():
    print(f"   [{label}] standard={info.get('standard')} pem_ok={info.get('pem_ok')}")

cp = Path("/home/pi/vinfast/test_exports/const.py")
if cp.exists():
    txt = cp.read_text(encoding="utf-8")
    print(f"\n   const.py: {len(txt)} byte")
    for line in txt.splitlines():
        if '"vin"' in line or '"email"' in line or '"device_id_by_email"' in line:
            print("     " + line.strip())
    # kiem tra const.py nay co import duoc khong
    spec = importlib.util.spec_from_file_location("_exp", cp)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
        print("   import OK | RENEWAL.vin =", m.RENEWAL["vin"],
              "| device_id_for =", m.device_id_for(m.RENEWAL["email"]))
    except Exception as exc:
        print("   IMPORT LỖI:", exc)

pem = Path("/home/pi/vinfast/test_exports/vinfast_private.pem")
if pem.exists():
    t = pem.read_text(encoding="utf-8")
    print(f"   PEM: {len(t)} byte, hop le =",
          t.startswith("-----BEGIN PRIVATE KEY-----") and t.strip().endswith("-----END PRIVATE KEY-----"))
