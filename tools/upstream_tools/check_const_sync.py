#!/usr/bin/env python3
"""
check_const_sync.py — Kiem tra HA va const.py co DONG BO khong.

Nguyen ly
---------
Moi gia tri HA **khong the tu lay** deu phai den tu nguon ngoai. Co 4 nguon:

  1. `const.py`            — hang so tinh (endpoint, device id mac dinh, UAA legacy)
  2. config entry options  — do nguoi dung nhap trong UI HA (email, password, UAA, PEM)
  3. `harvested_db.json`   — ket qua harvest (bo ba UAA + khoa theo tung tai khoan)
  4. `vinfast_const.json`  — const van hanh cua bo harvest (VIN, provider, device id)

Neu 4 nguon nay lech nhau thi HA chay bang gia tri KHAC voi thu nguoi dung tuong,
va trieu chung rat kho doan (vd sai device id -> `telemetry/app/ping` tra 403 y nhu
"xe dang ngu"). Script nay doi chieu va chi ro cho lech.

Chay:
    python3 check_const_sync.py            # tat ca tai khoan VinFast trong HA
    python3 check_const_sync.py --email a@b.c
    python3 check_const_sync.py --json

Exit code: 0 = dong bo, 1 = co lech.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/pi/.homeassistant/custom_components/vinfast")

CONST_FILE = Path("/home/pi/.homeassistant/custom_components/vinfast/const.py")
ENTRIES = Path("/home/pi/.homeassistant/.storage/core.config_entries")
DB_FILE = Path("/home/pi/vinfast/harvested_db.json")
VINFAST_CONST = Path("/home/pi/vinfast/vinfast_const.json")
PEM_FILE = Path("/home/pi/.homeassistant/custom_components/vinfast/vinfast_private.pem")


def mask(value: str, keep: int = 6) -> str:
    s = str(value or "")
    if not s:
        return "(rỗng)"
    if len(s) <= keep * 2:
        return s[:keep] + "…"
    return f"{s[:keep]}…{s[-4:]} (len={len(s)})"


def sha(value) -> str:
    return hashlib.sha256(str(value or "").encode()).hexdigest()[:12]


def load_const():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ha_const", CONST_FILE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ha_entries():
    cfg = json.loads(ENTRIES.read_text(encoding="utf-8"))
    out = []
    for e in cfg.get("data", {}).get("entries", []):
        if e.get("domain") != "vinfast":
            continue
        d = dict(e.get("data") or {})
        o = dict(e.get("options") or {})
        out.append({"title": e.get("title"), "data": d, "options": o,
                    "entry_id": e.get("entry_id")})
    return out


def pick(*sources):
    for s in sources:
        if s:
            return s
    return ""


ROWS: list[tuple[str, str, str, str, bool]] = []


def cmp_row(name: str, sources: dict, secret=False) -> bool:
    """sources: {nguon: gia tri}. Dong bo khi moi gia tri KHAC RONG bang nhau."""
    vals = {k: str(v or "").strip() for k, v in sources.items()}
    present = {k: v for k, v in vals.items() if v}
    ok = len({sha(v) for v in present.values()}) <= 1 if present else False
    shown = ", ".join(f"{k}={mask(v) if secret else (v or '(rỗng)')}"
                      for k, v in vals.items())
    ROWS.append((name, shown, "OK" if ok else "LỆCH", "", ok))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    C = load_const()
    entries = ha_entries()
    db = json.loads(DB_FILE.read_text(encoding="utf-8")) if DB_FILE.exists() else {}
    vc = json.loads(VINFAST_CONST.read_text(encoding="utf-8")) if VINFAST_CONST.exists() else {}

    print("=" * 92)
    print("KIỂM TRA ĐỒNG BỘ  const.py  ↔  config entry HA  ↔  harvested_db  ↔  vinfast_const")
    print("=" * 92)

    # ---------- A. Giá trị KHÔNG phụ thuộc tài khoản ----------
    print("\nA. HẰNG SỐ KHÔNG LẤY ĐƯỢC TỪ API (đọc thẳng từ const.py)")
    region = "VN"
    for e in entries:
        region = e["options"].get("region") or e["data"].get("region") or region
        break
    rc = C.REGION_CONFIG.get(region) or C.REGION_CONFIG["VN"]
    for key in ("AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "API_BASE", "AWS_REGION",
                "IOT_ENDPOINT", "EMQX_HOST", "EMQX_PORT"):
        has = key in rc and rc[key] not in (None, "")
        ROWS.append((f"REGION_CONFIG[{region}][{key}]", str(rc.get(key, "(THIẾU)")),
                     "OK" if has else "THIẾU", "", has))
        print(f"   {'OK ' if has else 'THIẾU'}  {key:18s} = {rc.get(key, '(THIẾU)')}")
    print(f"   device_id_for('x@y.z') = {C.device_id_for('x@y.z')} (mặc định DEVICE_ID)")

    # ---------- B. Từng tài khoản ----------
    targets = []
    for e in entries:
        email = (e["options"].get("email") or e["data"].get("email") or "").strip()
        if email:
            targets.append((email.lower(), e))
    if args.email:
        targets = [t for t in targets if t[0] == args.email.lower()]

    if not targets:
        print("\n(Không tìm thấy tài khoản VinFast nào trong config entry)")
    for email, e in targets:
        d, o = e["data"], e["options"]
        rec = db.get(email) or {}
        acc = (vc.get("accounts") or {}).get(email) or {}
        dev_map = {str(k).lower(): v for k, v in (C.DEVICE_ID_BY_EMAIL or {}).items()}

        print(f"\nB. TÀI KHOẢN {email}  (entry: {e['title']})")
        checks = [
            ("DEVICE_ID", {
                "const.py(DEVICE_ID_BY_EMAIL)": dev_map.get(email, ""),
                "const.py(DEVICE_ID)": C.DEVICE_ID,
                "HA option": pick(o.get("device_id"), d.get("device_id")),
                "harvested_db": rec.get("device_id"),
            }, False),
            ("UAA_CLIENT_INSTANCE_ID", {
                "const.py": C.UAA_CLIENT_INSTANCE_ID,
                "HA option": pick(o.get("uaa_client_instance_id"), d.get("uaa_client_instance_id")),
                "harvested_db": rec.get("uaa_client_instance_id"),
            }, False),
            ("UAA_TIMESTAMP", {
                "const.py": C.UAA_TIMESTAMP,
                "HA option": pick(o.get("uaa_timestamp"), d.get("uaa_timestamp")),
                "harvested_db": rec.get("uaa_timestamp"),
            }, False),
            ("UAA_SIGNATURE", {
                "HA option": pick(o.get("uaa_signature"), d.get("uaa_signature")),
                "harvested_db": rec.get("uaa_signature"),
            }, True),
            ("RSA private key", {
                "HA option": pick(o.get("vinfast_private_key"), d.get("vinfast_private_key")),
                "harvested_db": rec.get("private_key_pem"),
            }, True),
            ("password", {
                "HA entry": pick(o.get("password"), d.get("password")),
                "harvested_db": rec.get("password"),
            }, True),
            ("VIN", {
                "harvested_db": rec.get("vin"),
                "vinfast_const.json": acc.get("vin"),
            }, False),
        ]
        for name, sources, secret in checks:
            ok = cmp_row(name, sources, secret)
            mark = "OK  " if ok else "LỆCH"
            print(f"   [{mark}] {name}")
            for k, v in sources.items():
                print(f"           {k:30s} = {mask(v, 8) if secret else (v or '(rỗng)')}")

    # ---------- C. Tổng kết ----------
    bad = [r for r in ROWS if not r[4]]
    print("\n" + "=" * 92)
    print(f"KẾT QUẢ: {len(ROWS) - len(bad)}/{len(ROWS)} mục đồng bộ")
    if bad:
        print("MỤC LỆCH:")
        for name, shown, _, _, _ in bad:
            print(f"   - {name}")
        print("\nGợi ý: chạy lại bộ harvest (cổng 5556) rồi `POST /export_const` với")
        print("       `apply_main=true`, hoặc dán lại giá trị vào Options của HA.")
    print("=" * 92)

    if args.json:
        print(json.dumps({"rows": [{"name": n, "sources": s, "status": st}
                                   for n, s, st, _, _ in ROWS]},
                         ensure_ascii=False, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
