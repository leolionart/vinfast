import aiohttp
import uuid
import logging
import json
import math

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

def distance_total_unchanged(previous, current, tolerance=0.01):
    return previous is not None and abs(float(current) - float(previous)) < tolerance

def collect_gps_pair(pending, data, timestamp, max_skew=2.0):
    # [2.9.56] Chỉ ``00006_*`` là toạ độ thật. Bằng chứng: từ điển alias của server
    # (get-alias, 1836 mục) ghi rõ ``00006_00001_00000 = LOCATION_LATITUDE`` và
    # ``00006_00001_00001 = LOCATION_LONGITUDE``. Cặp dự phòng cũ
    # ``34185_00001_00001/00002`` KHÔNG phải toạ độ — đó là
    # ``VEHICLE_CRASH_STATUS_SIDE_LEFT_CRASH`` và ``..._REAR_CRASH`` (0/1), nên đã bỏ.
    for axis, keys in (
        ("lat", ("00006_00001_00000",)),
        ("lon", ("00006_00001_00001",)),
    ):
        for key in keys:
            if key in data:
                pending[axis] = (safe_float(data[key]), timestamp)
                break

    if "lat" not in pending or "lon" not in pending:
        return None

    lat, lat_time = pending["lat"]
    lon, lon_time = pending["lon"]
    if abs(lat_time - lon_time) > max_skew:
        pending.pop("lat" if lat_time < lon_time else "lon", None)
        return None

    pending.clear()
    return lat, lon

def gps_distance_m(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def route_gap_needs_repair(before, after, min_distance_m=250.0, min_gap_seconds=20.0):
    try:
        distance_m = gps_distance_m(float(before[0]), float(before[1]), float(after[0]), float(after[1]))
        gap_seconds = (float(after[3]) - float(before[3])) / 1000.0
        return distance_m > min_distance_m and gap_seconds > min_gap_seconds
    except (TypeError, ValueError, IndexError):
        return False

def merge_routed_gap(before, after, road):
    if not road or len(road) < 2:
        return []
    cleaned = [[float(point[0]), float(point[1])] for point in road]
    distances = [gps_distance_m(*start, *end) for start, end in zip(cleaned, cleaned[1:])]
    total = sum(distances)
    if total <= 0:
        return []
    before_speed, after_speed = safe_float(before[2]), safe_float(after[2])
    before_ts, after_ts = int(before[3]), int(after[3])
    merged, travelled = [], 0.0
    for index, point in enumerate(cleaned[1:-1], 1):
        travelled += distances[index - 1]
        ratio = travelled / total
        merged.append([
            round(point[0], 6), round(point[1], 6),
            round(before_speed + (after_speed - before_speed) * ratio),
            round(before_ts + (after_ts - before_ts) * ratio),
        ])
    return merged

def calculate_speed_band_efficiency(trips):
    bands = {name: {"distance": 0.0, "energy": 0.0} for name in ("0-30", "30-50", "50-70", "70-90", ">90")}
    for trip in trips:
        distance = safe_float(trip.get("distance"))
        energy = safe_float(trip.get("energy_used"))
        route = trip.get("route") or trip.get("raw_route") or []
        segments = []
        for before, after in zip(route, route[1:]):
            try:
                segment_distance = gps_distance_m(float(before[0]), float(before[1]), float(after[0]), float(after[1])) / 1000.0
                speed = max(0.0, (safe_float(before[2]) + safe_float(after[2])) / 2.0)
            except (TypeError, ValueError, IndexError):
                continue
            band = "0-30" if speed < 30 else "30-50" if speed < 50 else "50-70" if speed < 70 else "70-90" if speed < 90 else ">90"
            if 0 < segment_distance < 1:
                segments.append((band, segment_distance))

        route_distance = sum(value for _, value in segments)
        if distance > 0 and energy > 0 and route_distance > 0:
            scale = distance / route_distance
            for band, segment_distance in segments:
                weighted_distance = segment_distance * scale
                bands[band]["distance"] += weighted_distance
                bands[band]["energy"] += energy * weighted_distance / distance
        elif distance > 0 and energy > 0:
            duration = safe_float(trip.get("duration")) / 60.0
            speed = distance / duration if duration > 0 else 0
            band = "0-30" if speed < 30 else "30-50" if speed < 50 else "50-70" if speed < 70 else "70-90" if speed < 90 else ">90"
            bands[band]["distance"] += distance
            bands[band]["energy"] += energy

    return {band: round(values["energy"] / values["distance"] * 100, 1) if values["distance"] else 0 for band, values in bands.items()}

async def async_get_address_from_osm(session, lat, lon):
    try:
        # Sử dụng Photon (dữ liệu OSM) thay vì Nominatim vì Nominatim thường xuyên block/timeout
        url = f"https://photon.komoot.io/reverse?lon={lon}&lat={lat}"
        async with session.get(url, timeout=10) as res:
            if res.status == 200:
                data = await res.json()
                features = data.get("features", [])
                if features:
                    props = features[0].get("properties", {})
                    # Tạo chuỗi địa chỉ từ các thành phần
                    parts = []
                    for k in ["name", "street", "district", "city", "county", "state", "country"]:
                        if props.get(k) and props[k] not in parts:
                            parts.append(props[k])
                    addr = ", ".join(parts)
                    if addr and any(c.isalpha() for c in addr): return addr
    except Exception as e:
        _LOGGER.debug(f"VinFast Photon Helper Error: {e}")
        
    # Dự phòng bằng Nominatim
    try:
        headers = {"User-Agent": f"HA-VinFast-{uuid.uuid4().hex[:6]}"}
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18"
        async with session.get(url, headers=headers, timeout=5) as res:
            if res.status == 200:
                data = await res.json()
                addr = data.get("display_name")
                if addr and any(c.isalpha() for c in addr): return addr
    except Exception as e:
        _LOGGER.debug(f"VinFast Nominatim Helper Error: {e}")
        
    return None

async def async_get_osrm_route(session, lat1, lon1, lat2, lon2):
    """Lấy tuyến đường giữa 2 điểm (Dùng cho Smart Suggestion)"""
    for server in OSRM_SERVERS:
        try:
            url = f"{server}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&continue_straight=true"
            async with session.get(url, timeout=5) as res:
                if res.status == 200:
                    data = await res.json()
                    if data.get("code") == "Ok":
                        coords = data["routes"][0]["geometry"]["coordinates"]
                        return [[p[1], p[0]] for p in coords]
        except Exception as e:
            _LOGGER.debug(f"VinFast OSRM Helper Error ({server}): {e}")
    return None

async def async_get_weather_data(session, lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        async with session.get(url, timeout=10) as res:
            if res.status == 200:
                data = await res.json()
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
    except Exception as e:
        _LOGGER.debug(f"VinFast Weather Helper Error: {e}")
    return None
