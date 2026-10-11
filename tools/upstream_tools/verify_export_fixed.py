#!/usr/bin/env python3
"""Kiem chung ban xuat const.py sau khi va loi trung lap."""
import importlib.util
import json
import re
import urllib.request
from pathlib import Path

print("=== 1. Restart harvester da xong chua? Goi /export_const ===")
req = urllib.request.Request(
    "http://127.0.0.1:5556/export_const",
    data=json.dumps({"email": "thaitvad@gmail.com"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=120) as r:
    body = json.loads(r.read().decode())
print("   status:", body.get("status"))
for label, info in (body.get("written") or {}).items():
    print(f"   [{label}] standard={info.get('standard')} pem_ok={info.get('pem_ok')}")

p = Path("/home/pi/vinfast/test_exports/const.py")
txt = p.read_text(encoding="utf-8")
print(f"\n=== 2. const.py xuat ra: {len(txt)} byte ===")

fails = []


def chk(cond, msg):
    print(f"   [{'OK  ' if cond else 'LỖI '}] {msg}")
    if not cond:
        fails.append(msg)


# a) CONF_UAA_* PHAI la ten khoa option, KHONG phai gia tri UAA
want_conf = {
    "CONF_UAA_CLIENT_INSTANCE_ID": "uaa_client_instance_id",
    "CONF_UAA_SIGNATURE": "uaa_signature",
    "CONF_UAA_TIMESTAMP": "uaa_timestamp",
    "CONF_VINFAST_PRIVATE_KEY": "vinfast_private_key",
}
print("\n   --- a) CONF_* giữ đúng TÊN KHOÁ OPTION ---")
for k, want in want_conf.items():
    m = re.search(rf'^{k}\s*=\s*"([^"]*)"', txt, re.M)
    got = m.group(1) if m else "(không thấy)"
    chk(got == want, f"{k} = {got!r} (mong đợi {want!r})")

# b) UAA_* PHAI co gia tri THAT
print("\n   --- b) UAA_* giữ GIÁ TRỊ THẬT ---")
for k in ("UAA_CLIENT_INSTANCE_ID", "UAA_TIMESTAMP", "UAA_SIGNATURE"):
    m = re.search(rf'^(?<![A-Z_]){k}\s*=\s*"([^"]*)"', txt, re.M)
    val = m.group(1) if m else ""
    chk(bool(val), f"{k} = {val[:40]}{'…' if len(val) > 40 else ''}")

# c) Khong con trung lap: CONF_ va UAA_ phai KHAC nhau
print("\n   --- c) KHÔNG còn trùng lặp ---")
cid_conf = re.search(r'^CONF_UAA_CLIENT_INSTANCE_ID\s*=\s*"([^"]*)"', txt, re.M)
cid_uaa = re.search(r'^(?<![A-Z_])UAA_CLIENT_INSTANCE_ID\s*=\s*"([^"]*)"', txt, re.M)
chk(bool(cid_conf and cid_uaa and cid_conf.group(1) != cid_uaa.group(1)),
    f"CONF_({cid_conf.group(1) if cid_conf else '?'}) ≠ UAA_({(cid_uaa.group(1) if cid_uaa else '?')[:20]}…)")

# d) EMQX co mat
print("\n   --- d) Cấu hình MQTT có mặt ---")
chk('"EMQX_HOST": "ccp-mqtt.vinfast.vn"' in txt, "EMQX_HOST = ccp-mqtt.vinfast.vn")
chk('"EMQX_PORT": 8884' in txt, "EMQX_PORT = 8884")

# e) import duoc va chay dung
print("\n   --- e) File import được và chạy đúng ---")
try:
    spec = importlib.util.spec_from_file_location("exp", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    chk(m.CONF_UAA_CLIENT_INSTANCE_ID == "uaa_client_instance_id",
        f"import: CONF_UAA_CLIENT_INSTANCE_ID = {m.CONF_UAA_CLIENT_INSTANCE_ID!r}")
    chk(bool(m.UAA_CLIENT_INSTANCE_ID), f"import: UAA_CLIENT_INSTANCE_ID = {m.UAA_CLIENT_INSTANCE_ID[:20]}…")
    chk(m.REGION_CONFIG["VN"]["EMQX_HOST"] == "ccp-mqtt.vinfast.vn",
        "import: REGION_CONFIG['VN']['EMQX_HOST']")
    chk(m.device_id_for("thaitvad@gmail.com") == "8feb7998824e390b",
        "import: device_id_for('thaitvad@gmail.com')")
except Exception as exc:
    chk(False, f"import lỗi: {type(exc).__name__}: {exc}")

print("\n" + "=" * 70)
print(f"KẾT QUẢ: {'TẤT CẢ PASS' if not fails else f'{len(fails)} LỖI'}")
for f in fails:
    print("   -", f)
print("=" * 70)
