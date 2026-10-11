#!/usr/bin/env python3
"""
Kiem chung: config_flow doc duoc MQTT server tu const + override tu options.
Chay tren Pi (dung venv vi config_flow can HA).
"""
import importlib.util
import json
import sys
from pathlib import Path

DIR = Path("/home/pi/.homeassistant/custom_components/vinfast")
sys.path.insert(0, str(DIR))

print("=== 1. const.py: ham emqx_server ===")
spec = importlib.util.spec_from_file_location("c", DIR / "const.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
print("   CONF_EMQX_HOST =", c.CONF_EMQX_HOST)
print("   CONF_EMQX_PORT =", c.CONF_EMQX_PORT)
cases = [
    ("mặc định VN", "VN", None),
    ("vùng US", "US", None),
    ("UI ghi đè host", "VN", {c.CONF_EMQX_HOST: "mqtt.moi.vn"}),
    ("UI ghi đè cả hai", "VN", {c.CONF_EMQX_HOST: "mqtt.moi.vn", c.CONF_EMQX_PORT: 9999}),
    ("UI port rác", "VN", {c.CONF_EMQX_PORT: "abc"}),
    ("vùng lạ", "ZZ", None),
]
for name, region, opts in cases:
    print(f"   {name:22s} -> {c.emqx_server(region, opts)}")

print("\n=== 2. config_flow.py: co import + truong MQTT chua? ===")
cf = (DIR / "config_flow.py").read_text(encoding="utf-8")
for token in ("CONF_EMQX_HOST", "CONF_EMQX_PORT", "emqx_server(",
              "vol.Optional(CONF_EMQX_HOST", "vol.Optional(CONF_EMQX_PORT"):
    print(f"   {'CÓ ' if token in cf else 'THIẾU'} {token}")

print("\n=== 3. api_mqtt.py: dung emqx_server + options? ===")
mq = (DIR / "api_mqtt.py").read_text(encoding="utf-8")
for token in ("emqx_server(", 'getattr(self.core, "options"', 'self.client.connect(_host, _port'):
    print(f"   {'CÓ ' if token in mq else 'THIẾU'} {token}")
print("   còn sót '_rc'? ", "_rc" in mq)

print("\n=== 4. translations ===")
for lang in ("en", "vi"):
    p = DIR / "translations" / f"{lang}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    data = d.get("options", {}).get("step", {}).get("init", {}).get("data", {})
    print(f"   {lang}.json: {len(data)} nhãn | emqx_host = {data.get('emqx_host', '(THIẾU)')}")

print("\n=== 5. Core co nhan options khong? ===")
ap = (DIR / "api.py").read_text(encoding="utf-8")
i = ap.find("def __init__")
seg = ap[i:i + 700]
for line in seg.splitlines():
    if "options" in line or "self.region" in line:
        print("   ", line.strip()[:100])
