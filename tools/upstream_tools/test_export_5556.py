#!/usr/bin/env python3
"""Kiem thu xuat const.py + PEM qua harvester 5556 va kiem tra noi dung."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:5556"


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


print("=== 1. GET / (service song?) ===")
try:
    with urllib.request.urlopen(BASE + "/", timeout=20) as r:
        print("   HTTP", r.status)
except Exception as e:
    print("   LỖI:", e)

print("\n=== 2. POST /export_const (apply_main=false) ===")
st, body = post("/export_const", {"email": "thaitvad@gmail.com"})
print("   HTTP", st)
if isinstance(body, dict):
    for k in ("status", "message"):
        if k in body:
            print(f"   {k}: {body[k]}")
    for label, info in (body.get("written") or {}).items():
        print(f"   [{label}] dir={info.get('dir')}")
        print(f"      standard={info.get('standard')}  pem_ok={info.get('pem_ok')}  ref={info.get('reference')}")
else:
    print("   ", str(body)[:300])

print("\n=== 3. Kiem tra const.py xuat ra ===")
for p in (Path("/home/pi/vinfast/test_exports/const.py"),):
    if not p.exists():
        print("   KHONG CO:", p)
        continue
    txt = p.read_text(encoding="utf-8")
    print(f"   {p}  ({len(txt)} byte)")
    for key in ("RENEWAL", "device_id_for", '"vin"', '"email"', "CONF_UAA_CLIENT_INSTANCE_ID"):
        print(f"      {key:32s} {'CO' if key in txt else 'THIEU'}")
    # in khoi RENEWAL
    i = txt.find("RENEWAL = {")
    if i >= 0:
        print("   --- khoi RENEWAL xuat ra ---")
        for line in txt[i:i + 1400].splitlines()[:32]:
            print("      " + line)

print("\n=== 4. Kiem tra PEM xuat ra ===")
pem = Path("/home/pi/vinfast/test_exports/vinfast_private.pem")
if pem.exists():
    t = pem.read_text(encoding="utf-8")
    print(f"   {pem}  ({len(t)} byte)")
    print("   BEGIN:", t.splitlines()[0] if t else "")
    print("   END  :", t.strip().splitlines()[-1] if t else "")
    owner = Path(str(pem) + ".owner")
    print("   owner:", owner.read_text().strip() if owner.exists() else "(khong co)")
else:
    print("   KHONG CO:", pem)
