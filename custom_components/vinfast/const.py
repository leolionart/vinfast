import os

DOMAIN = "vinfast"
CONF_MAPBOX_TOKEN = "mapbox_token"
CONF_STADIA_TOKEN = "stadia_token"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_GEMINI_API_KEY = "gemini_api_key"
CONF_REGION = "region"
CONF_LANGUAGE = "language"

# Cấu hình xác thực UAA & WAF (UI Config Entry)
CONF_UAA_CLIENT_INSTANCE_ID = "uaa_client_instance_id"
CONF_UAA_SIGNATURE = "uaa_signature"
CONF_UAA_TIMESTAMP = "uaa_timestamp"
CONF_VINFAST_PRIVATE_KEY = "vinfast_private_key"

# Máy chủ MQTT — cho phép ghi đè từ UI khi VinFast đổi máy chủ (không cần sửa code).
CONF_EMQX_HOST = "emqx_host"
CONF_EMQX_PORT = "emqx_port"

# ==========================================
# CẤU HÌNH ĐA VÙNG (MULTI-REGION)
# ==========================================
# `EMQX_HOST`/`EMQX_PORT`: máy chủ MQTT EMQX. KHÔNG endpoint nào trả về hai giá trị
# này — VinFast đổi máy chủ thì phải sửa ở đây rồi khởi động lại HA.
REGION_CONFIG = {
    "VN": {
        "AUTH0_DOMAIN": "https://vin3s.au.auth0.com",
        "AUTH0_CLIENT_ID": "jE5xt50qC7oIh1f32qMzA6hGznIU5mgH",
        "API_BASE": "https://mobile.connected-car.vinfast.vn",
        "AWS_REGION": "ap-southeast-1",
        "COGNITO_POOL_ID": "ap-southeast-1:c6537cdf-92dd-4b1f-99a8-9826f153142a",
        "IOT_ENDPOINT": "prod.iot.connected-car.vinfast.vn",
        "EMQX_HOST": "ccp-mqtt.vinfast.vn",
        "EMQX_PORT": 8884
    },
    "US": {
        "AUTH0_DOMAIN": "https://vin3s.us.auth0.com", 
        "AUTH0_CLIENT_ID": "jE5xt50qC7oIh1f32qMzA6hGznIU5mgH", 
        "API_BASE": "https://api.us.vinfastauto.com",
        "AWS_REGION": "us-east-1",
        "COGNITO_POOL_ID": "us-east-1:xxxxxx-xxxx-xxxx-xxxx",
        "IOT_ENDPOINT": "prod.iot.us.connected-car.vinfast.vn",
        "EMQX_HOST": "ccp-mqtt.us.vinfast.vn",
        "EMQX_PORT": 8884
    }
}

# X-Device-Identifier mặc định. Quyền gọi `telemetry/app/ping` gắn với CẶP
# (tài khoản, device id): sai device id trả 403 y như xe đang ngủ.
DEVICE_ID = "8feb7998824e390b"

#: Device id riêng theo tài khoản (tài khoản không có ở đây dùng DEVICE_ID).
#: Bộ harvest ở cổng 5556 điền tự động khi xuất const.py.
DEVICE_ID_BY_EMAIL = {
    "thaitvad@gmail.com": "8feb7998824e390b",
}


def device_id_for(email, fallback=None):
    """Device id hiệu lực cho một tài khoản."""
    mapped = {str(k).lower(): v for k, v in DEVICE_ID_BY_EMAIL.items()}
    return mapped.get(str(email or "").strip().lower()) or fallback or DEVICE_ID


def emqx_server(region="VN", options=None):
    """(host, port) máy chủ MQTT EMQX — ba tầng ưu tiên.

    1. tuỳ chọn người dùng nhập trong UI (`emqx_host` / `emqx_port`),
    2. `REGION_CONFIG[region]` trong file này,
    3. mặc định cứng (giữ nguyên hành vi cũ).

    VinFast đổi máy chủ thì nhập ở UI là xong, không phải sửa code rồi khởi động lại.
    """
    rc = REGION_CONFIG.get(str(region or "VN").upper()) or REGION_CONFIG["VN"]
    opts = options or {}
    host = (str(opts.get(CONF_EMQX_HOST) or "").strip()
            or rc.get("EMQX_HOST") or "ccp-mqtt.vinfast.vn")
    try:
        port = int(opts.get(CONF_EMQX_PORT) or rc.get("EMQX_PORT") or 8884)
    except (TypeError, ValueError):
        port = int(rc.get("EMQX_PORT") or 8884)
    return host, port


BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WWW_DIR = os.path.join(BASE_PATH, "www")
MOCK_FILE = "/config/www/vinfast_mock_data.json"

# ==========================================
# TƯƠNG THÍCH NGƯỢC (LEGACY HARDCODE FALLBACK)
# ==========================================
UAA_CLIENT_INSTANCE_ID = ""
UAA_TIMESTAMP = ""
UAA_SIGNATURE = ""
