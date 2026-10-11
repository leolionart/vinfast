#!/usr/bin/env python3
"""Dien nhan day du cho config_flow + options flow (EN/VI), gom 2 truong MQTT moi."""
import json
import shutil
import time
from pathlib import Path

DIR = Path("/home/pi/.homeassistant/custom_components/vinfast/translations")

# key -> (nhan EN, nhan VI)
LABELS = {
    "email": ("Email address", "Địa chỉ email"),
    "password": ("Password", "Mật khẩu"),
    "region": ("Region", "Khu vực"),
    "language": ("Language", "Ngôn ngữ"),
    "gemini_api_key": ("Gemini API key", "Khoá Gemini API"),
    "gemini_model": ("Gemini model", "Model Gemini"),
    "mapbox_token": ("Mapbox token", "Token Mapbox"),
    "stadia_token": ("Stadia token", "Token Stadia"),
    "emqx_host": ("MQTT server host (blank = use const.py)",
                  "Máy chủ MQTT: host (để trống = dùng const.py)"),
    "emqx_port": ("MQTT server port (blank = use const.py)",
                  "Máy chủ MQTT: port (để trống = dùng const.py)"),
    "cost_per_kwh": ("Electricity price per kWh (VND)", "Giá điện mỗi kWh (VNĐ)"),
    "gas_price": ("Petrol price (VND/litre)", "Giá xăng (VNĐ/lít)"),
    "uaa_client_instance_id": ("UAA clientInstanceId", "UAA clientInstanceId"),
    "uaa_signature": ("UAA signature", "UAA signature"),
    "uaa_timestamp": ("UAA timestamp", "UAA timestamp"),
    "vinfast_private_key": ("VinFast private key (PEM)", "Khoá riêng VinFast (PEM)"),
    "control_private_key_pem": ("Remote-control private key (PEM)",
                                "Khoá riêng điều khiển (PEM)"),
    "control_share_key": ("Remote-control share key", "Khoá chia sẻ điều khiển"),
    "control_session_id": ("Remote-control session id", "Session ID điều khiển"),
    "control_master_profile": ("Use master profile", "Dùng hồ sơ chủ xe"),
    "control_wakeup_timeout_ms": ("Wake-up timeout (ms)", "Thời gian chờ đánh thức (ms)"),
    "control_advanced_buttons": ("Enable advanced control buttons",
                                 "Bật nút điều khiển mở rộng"),
    # config flow buoc dau
    "vehicle": ("Vehicle", "Xe"),
    "vin": ("VIN", "Số VIN"),
}

TITLES = {
    "en": {
        "config.user.title": "VinFast account login",
        "config.user.desc": "Enter the email and password you use in the VinFast app.",
        "config.select.title": "Select your vehicle",
        "config.select.desc": "Vehicles found in your account. Pick one to add.",
        "config.init.title": "VinFast extended setup",
        "options.init.title": "VinFast configuration",
        "options.init.desc": "Change the integration settings, including the MQTT server.",
    },
    "vi": {
        "config.user.title": "Đăng nhập tài khoản VinFast",
        "config.user.desc": "Nhập email và mật khẩu bạn dùng trên app VinFast.",
        "config.select.title": "Chọn xe của bạn",
        "config.select.desc": "Các xe tìm thấy trong tài khoản. Chọn một xe để thêm.",
        "config.init.title": "Cấu hình Mở rộng VinFast",
        "options.init.title": "Cấu hình VinFast",
        "options.init.desc": "Thay đổi cấu hình tích hợp, gồm cả máy chủ MQTT.",
    },
}

for lang, idx in (("en", 0), ("vi", 1)):
    p = DIR / f"{lang}.json"
    if not p.exists():
        # tạo mới từ en nếu thiếu
        base = json.loads((DIR / "en.json").read_text(encoding="utf-8"))
        d = json.loads(json.dumps(base, ensure_ascii=False))
    else:
        d = json.loads(p.read_text(encoding="utf-8"))
        bak = p.with_suffix(f".json.bak2_{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(p, bak)

    def data_at(path, create=True):
        node = d
        for part in path:
            if create:
                node = node.setdefault(part, {})
            else:
                node = node.get(part, {})
                if not isinstance(node, dict):
                    return {}
        return node.setdefault("data", {}) if create else node.get("data", {})

    for path in (("config", "step", "user"), ("config", "step", "select_vehicle"),
                 ("config", "step", "init"), ("options", "step", "init")):
        node = d
        for part in path:
            node = node.setdefault(part, {})
        node.setdefault("data", {})
        for key, pair in LABELS.items():
            node["data"][key] = pair[idx]

    t = TITLES[lang]
    d["config"]["step"]["user"]["title"] = t["config.user.title"]
    d["config"]["step"]["user"]["description"] = t["config.user.desc"]
    d["config"]["step"]["select_vehicle"]["title"] = t["config.select.title"]
    d["config"]["step"]["select_vehicle"]["description"] = t["config.select.desc"]
    d["config"]["step"]["init"]["title"] = t["config.init.title"]
    d["options"]["step"]["init"]["title"] = t["options.init.title"]
    d["options"]["step"]["init"]["description"] = t["options.init.desc"]

    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    n = len(d["options"]["step"]["init"]["data"])
    print(f"  [OK] {p.name}: options.init.data = {n} trường")
    print(f"       emqx_host = {d['options']['step']['init']['data']['emqx_host']}")
