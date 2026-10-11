#!/usr/bin/env python3
"""Tao vi.json tu en.json (dich nhan cho 2 truong MQTT; phan con lai giu nguyen)."""
import json
from pathlib import Path

DIR = Path("/home/pi/.homeassistant/custom_components/vinfast/translations")
en = json.loads((DIR / "en.json").read_text(encoding="utf-8"))

# Dịch nhãn options init sang tiếng Việt
VI = {
    "email": "Địa chỉ email",
    "password": "Mật khẩu",
    "region": "Khu vực",
    "language": "Ngôn ngữ",
    "gemini_api_key": "Khoá Gemini API",
    "gemini_model": "Model Gemini",
    "mapbox_token": "Token Mapbox",
    "stadia_token": "Token Stadia",
    "emqx_host": "Máy chủ MQTT (host) — để trống = dùng const.py",
    "emqx_port": "Máy chủ MQTT (port) — để trống = dùng const.py",
    "cost_per_kwh": "Giá điện mỗi kWh (VNĐ)",
    "gas_price": "Giá xăng (VNĐ/lít)",
    "uaa_client_instance_id": "UAA clientInstanceId",
    "uaa_signature": "UAA signature",
    "uaa_timestamp": "UAA timestamp",
    "vinfast_private_key": "Khoá riêng VinFast (PEM)",
    "control_private_key_pem": "Khoá riêng điều khiển (PEM)",
    "control_share_key": "Khoá chia sẻ điều khiển",
    "control_session_id": "Session ID điều khiển",
    "control_master_profile": "Dùng hồ sơ chủ xe",
    "control_wakeup_timeout_ms": "Thời gian chờ đánh thức (ms)",
    "control_advanced_buttons": "Bật nút điều khiển mở rộng",
}

vi = json.loads(json.dumps(en, ensure_ascii=False))
step = vi.setdefault("options", {}).setdefault("step", {}).setdefault("init", {})
data = step.setdefault("data", {})
for k, v in VI.items():
    if k in data:
        data[k] = v
if "title" in step:
    step["title"] = "Cấu hình VinFast"
if "description" in step:
    step["description"] = "Thay đổi cấu hình tích hợp VinFast."

p = DIR / "vi.json"
p.write_text(json.dumps(vi, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Đã tạo {p} ({p.stat().st_size} byte)")
print("Các trường có nhãn tiếng Việt:")
for k in sorted(data):
    mark = "VI" if k in VI else "--"
    print(f"   [{mark}] {k}: {data[k]}")
