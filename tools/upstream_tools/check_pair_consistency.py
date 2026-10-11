#!/usr/bin/env python3
"""
Voi tai khoan bi lech: kiem tra ben nao TU NHAT QUAN (chu ky UAA khop voi khoa).
Mot cap (clientInstanceId, timestamp, signature, private_key) chi dung duoc khi
`signature` duoc ky bang dung `private_key` do.
"""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/pi/vinfast")
import vinfast_login as vl

ENTRIES = Path("/home/pi/.homeassistant/.storage/core.config_entries")
DB_FILE = Path("/home/pi/vinfast/harvested_db.json")
EMAIL = "gambt90@gmail.com"

cfg = json.loads(ENTRIES.read_text(encoding="utf-8"))
entry = next(x for x in cfg["data"]["entries"]
             if "gambt90" in str(x.get("data", {})) or "TG Family" == x.get("title"))
d, o = entry.get("data") or {}, entry.get("options") or {}
db = json.loads(DB_FILE.read_text(encoding="utf-8"))
rec = db.get(EMAIL) or db.get(EMAIL.lower()) or {}


def pick(*vals):
    for v in vals:
        if v:
            return v
    return ""


sources = {
    "HA config entry": {
        "cid": pick(o.get("uaa_client_instance_id"), d.get("uaa_client_instance_id")),
        "ts": pick(o.get("uaa_timestamp"), d.get("uaa_timestamp")),
        "sig": pick(o.get("uaa_signature"), d.get("uaa_signature")),
        "pem": pick(o.get("vinfast_private_key"), d.get("vinfast_private_key")),
    },
    "harvested_db.json": {
        "cid": rec.get("uaa_client_instance_id", ""),
        "ts": rec.get("uaa_timestamp", ""),
        "sig": rec.get("uaa_signature", ""),
        "pem": rec.get("private_key_pem", ""),
    },
}

print(f"Tài khoản: {EMAIL}\n")
for name, s in sources.items():
    print(f"=== {name} ===")
    print(f"  clientInstanceId: {s['cid']}")
    print(f"  timestamp       : {s['ts']}")
    print(f"  signature       : {(s['sig'] or '')[:40]}…")
    print(f"  PEM             : {len(s['pem'])} ký tự")
    key = vl._key_from_pem_text(s["pem"]) if s["pem"] else None
    if not key:
        print("  -> KHÔNG đọc được khoá")
        print()
        continue
    expect = vl.sign_uaa(key, s["cid"], s["ts"]) if (s["cid"] and s["ts"]) else None
    ok = bool(expect and expect.strip() == str(s["sig"]).strip())
    print(f"  -> chữ ký ký lại bằng khoá này: {'KHỚP ✓ (cặp tự nhất quán)' if ok else 'KHÔNG KHỚP ✗ (khoá và bộ ba LỆCH NHAU)'}")
    if expect and not ok:
        print(f"     chờ đợi: {expect[:40]}…")
        print(f"     đang có: {str(s['sig'])[:40]}…")
    print()
