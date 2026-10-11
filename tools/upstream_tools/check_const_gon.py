#!/usr/bin/env python3
"""Kiem tra const.py gon: giu du hang so cu, chi them dung thu HA dung."""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "c", "/home/pi/.homeassistant/custom_components/vinfast/const.py")
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except Exception as exc:
    print("  IMPORT LỖI:", exc)
    sys.exit(1)

legacy = ["DOMAIN", "CONF_MAPBOX_TOKEN", "CONF_STADIA_TOKEN", "CONF_EMAIL", "CONF_PASSWORD",
          "CONF_GEMINI_API_KEY", "CONF_REGION", "CONF_LANGUAGE", "CONF_UAA_CLIENT_INSTANCE_ID",
          "CONF_UAA_SIGNATURE", "CONF_UAA_TIMESTAMP", "CONF_VINFAST_PRIVATE_KEY",
          "REGION_CONFIG", "DEVICE_ID", "BASE_PATH", "WWW_DIR", "MOCK_FILE",
          "UAA_CLIENT_INSTANCE_ID", "UAA_TIMESTAMP", "UAA_SIGNATURE"]
missing = [k for k in legacy if not hasattr(m, k)]
print(f"  Hằng số legacy còn đủ: {len(legacy) - len(missing)}/{len(legacy)}")
if missing:
    print("  THIẾU:", missing)

print("  Thêm mới:", [k for k in ("DEVICE_ID_BY_EMAIL", "device_id_for") if hasattr(m, k)])
print("  device_id_for('thaitvad@gmail.com') =", m.device_id_for("thaitvad@gmail.com"))
print("  device_id_for('khac@x.yz')          =", m.device_id_for("khac@x.yz"))

src = open("/home/pi/.homeassistant/custom_components/vinfast/const.py",
           encoding="utf-8").read()
print("  Còn RENEWAL (thừa)?", "RENEWAL" in src)
print("  Còn khoá 'vin'/'email' (thừa)?", '"vin"' in src or '"email":' in src)
print("  Số dòng:", len(src.splitlines()))
