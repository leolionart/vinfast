import requests
import time
import uuid
import logging
import json
import sys

_LOGGER = logging.getLogger(__name__)

# DANH SÁCH MÁY CHỦ BẢN ĐỒ MIỄN PHÍ DỰ PHÒNG
OSRM_SERVERS = [
    "https://routing.openstreetmap.de/routed-car", 
    "http://router.project-osrm.org",              
]

def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "": return default
        return float(val)
    except Exception: return default

def get_address_from_osm(lat, lon):
    try:
        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18", headers={"User-Agent": f"HA-VinFast-{uuid.uuid4().hex[:6]}"}, timeout=5)
        if res.status_code == 200: 
            addr = res.json().get("display_name")
            if addr and any(c.isalpha() for c in addr): return addr
    except Exception: pass
    return None

def get_osrm_route(lat1, lon1, lat2, lon2):
    """Lấy tuyến đường giữa 2 điểm (Dùng cho Smart Suggestion)"""
    try:
        for server in OSRM_SERVERS:
            url = f"{server}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&continue_straight=true"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("code") == "Ok":
                    coords = data["routes"][0]["geometry"]["coordinates"]
                    return [[p[1], p[0]] for p in coords]
    except Exception: pass
    return None

def get_weather_data(lat, lon):
    try:
        res = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=10)
        if res.status_code == 200:
            data = res.json()
            current = data.get("current_weather", {})
            temp = current.get("temperature")
            code = current.get("weathercode", 0)
            if temp is not None:
                condition = "Quang đãng"
                if code in [1, 2, 3]: condition = "Có mây"
                elif code in [45, 48]: condition = "Sương mù"
                elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: condition = "Trời mưa"
                elif code in [71, 73, 75, 85, 86]: condition = "Tuyết rơi"
                elif code in [95, 96, 99]: condition = "Sấm chớp"
                
                hvac = "Bình thường"
                if temp >= 35: hvac = "Rất cao (Làm mát tối đa)"
                elif temp >= 30: hvac = "Cao (Làm mát nhanh)"
                elif temp <= 15: hvac = "Cao (Sưởi ấm)"
                return {"temp": temp, "condition": condition, "hvac": hvac, "code": code}
    except: pass
    return None
    
def _build_chat_completions_url(base_url):
    clean = (base_url or "").strip().rstrip("/")
    if not clean:
        return None
    lower = clean.lower()
    if lower.endswith("/chat/completions"):
        return clean
    if lower.endswith("/v1"):
        return f"{clean}/chat/completions"
    return f"{clean}/v1/chat/completions"

def _extract_chat_content(response_json):
    choices = response_json.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return str(content).strip()

def get_ai_advice(base_url, api_key, ai_model, mode, data_payload, context_data):
    if not api_key or api_key.strip() == "":
        return "Vui lòng nhập AI API Key."
    temp = context_data.get("temp", "Không rõ")
    cond = context_data.get("cond", "Không rõ")
    hvac = context_data.get("hvac", "Bình thường")
    expected_km_per_1 = context_data.get("expected_km_per_1", 2.1)

    system_prompt = (
        "Bạn là cố vấn lái xe điện VinFast. "
        "Trả lời ngắn, thực dụng, tập trung vào an toàn, hiệu suất pin và điều hoa. "
        "Không dùng markdown, không giải thích dài."
    )

    if mode == "weather" and data_payload:
        prompt = f"CẢNH BÁO THỜI TIẾT: Nhiệt độ {data_payload.get('temp', temp)}C, {data_payload.get('cond', cond)}. Hãy viết 1 câu khuyên lái xe xe điện VinFast cách đi an toàn và chỉnh điều hòa."
    elif mode == "anomaly" and data_payload:
        prompt = f"SỤT PIN: Mất {round(data_payload.get('drop', 0), 2)}% để đi {round(data_payload.get('dist', 0), 2)}km ({round(data_payload.get('speed', 0), 1)}km/h). Gấp {round(expected_km_per_1, 2)}km bình thường. Nhiệt độ: {temp}C. Hãy đưa lời khuyên (1 câu)."
    else:
        prompt = f"TỔNG KẾT CHUYẾN ĐI: {context_data.get('trip_dist', 0)}km, tốc độ {context_data.get('trip_avg_speed', 0)}km/h. Thời tiết: {temp}C, {cond}. Đánh giá hiệu suất và cho lời khuyên (1 câu)."

    url = _build_chat_completions_url(base_url)
    if not url:
        return "Vui lòng nhập AI Base URL."

    payload = {
        "model": ai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 120,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}",
    }

    for attempt in range(3):
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                text = _extract_chat_content(res.json())
                return text.replace("*", "").strip() if text else "Lỗi phản hồi AI."
            if res.status_code in (400, 401, 403, 404):
                body = res.text[:200].strip()
                return f"❌ AI API lỗi {res.status_code}: {body}" if body else f"❌ AI API lỗi {res.status_code}."
            if attempt < 2: time.sleep(3)
        except: 
            if attempt < 2: time.sleep(3)
    return "❌ Lỗi kết nối AI API."
