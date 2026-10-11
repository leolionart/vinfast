#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
waze_alerts.py — Client dữ liệu cảnh báo Waze Mod cho component VinFast.

Luồng dữ liệu (đã kiểm chứng đầu-cuối):
    manifest JSON  ->  artifact AES-256-GCM  ->  gzip  ->  protobuf
    ->  danh sách cảnh báo (id, type, lat, lon, trigger_distance_m, side_rule)

Bảo mật / xác thực:
  * Khoá AES-256 = 32 byte đầu SHA-256 của chứng chỉ ký APK mà mod dùng làm
    "khoá danh tính" (native lib từ chối nếu chữ ký app không khớp). Đây KHÔNG
    phải bí mật của người dùng; nó suy ra được từ chính APK công khai.
  * Kiểm tra SHA-256 artifact theo manifest và SHA-256 plaintext sau giải nén.
  * Ed25519 signature trong manifest KHÔNG được xác minh ở đây (cần public key
    của mod); bù lại có 2 lớp SHA-256 + AES-GCM auth tag.

Module KHÔNG import Home Assistant để test offline được.
"""
from __future__ import annotations

import asyncio
import base64
import gzip
import hashlib
import json
import logging
import math
import struct
import time
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

WAZE_BASE = "https://wazemod.io.vn"
WAZE_BASE_FALLBACK = "https://wazemod.chisadin.id.vn"
WAZE_UA = "WazeMod/5.24.5.0"
SIGNING_CERT_SHA256 = (
    "4305d945e2a61cd6e36e81ceb8bc64ac083112a18e45e5e550feabd5b7f48f8a"
)
_AES_KEY = bytes.fromhex(SIGNING_CERT_SHA256)
_POINT_MANIFEST = "/api/client/comments/manifest"
_DOWNLOAD_LIMIT = 16 * 1024 * 1024
_HTTP_TIMEOUT = 30

# Bảng mã cảnh báo (trích từ com.waze.gw.HudAlertCodec)
ALERT_TYPES: dict[int, tuple[str, str]] = {
    1: ("POLICE_CHECKPOINT", "Cảnh sát / Trạm kiểm soát"),
    2: ("ACCIDENT_CRASH", "Tai nạn giao thông"),
    3: ("TRAFFIC_LIGHT_CAMERA", "Camera đèn đỏ"),
    4: ("SPEED_CAMERA", "Camera bắn tốc độ"),
    5: ("BAD_WEATHER", "Thời tiết xấu"),
    6: ("TRAFFIC_JAM", "Ùn tắc giao thông"),
    7: ("ROAD_CLOSURE", "Đóng đường"),
    8: ("SPEED_LIMIT", "Biển giới hạn tốc độ"),
    9: ("NO_PASSING", "Cấm vượt"),
    10: ("END_NO_PASSING", "Hết cấm vượt"),
    11: ("RAILWAY_CROSSING", "Giao cắt đường sắt"),
    12: ("TOLL_BOOTH", "Trạm thu phí"),
    13: ("STOPPED_VEHICLE", "Xe dừng đỗ / Sự cố ven đường"),
    14: ("CONSTRUCTION", "Công trường thi công"),
    15: ("POTHOLE", "Ổ gà"),
    16: ("WEATHER_GENERAL", "Thời tiết chung"),
    17: ("HAZARD_GENERAL", "Nguy hiểm chung trên đường"),
    18: ("INTERSECTION", "Giao lộ nguy hiểm"),
    19: ("EXPRESSWAY_EXIT", "Lối ra cao tốc"),
    20: ("EXPRESSWAY_REST_AREA", "Trạm dừng nghỉ cao tốc"),
    21: ("EXPRESSWAY_ENTRY", "Lối vào cao tốc"),
    22: ("END_SPEED_LIMIT", "Hết giới hạn tốc độ"),
    23: ("COMBINED_CAMERA", "Camera phạt nguội tổng hợp"),
    24: ("AVERAGE_SPEED_ZONE", "Khu vực kiểm tra tốc độ trung bình"),
    25: ("DISTANCE_CAMERA", "Camera đo khoảng cách an toàn"),
    26: ("BUS_LANE_CAMERA", "Camera phạt lấn làn xe buýt"),
    27: ("NOISE_CAMERA", "Camera phạt tiếng ồn"),
    28: ("STOP_SIGN_CAMERA", "Camera biển báo dừng đỗ"),
    29: ("SEATBELT_CAMERA", "Camera phạt không thắt dây an toàn"),
    30: ("PHONE_CAMERA", "Camera phạt dùng điện thoại"),
    31: ("DUMMY_CAMERA", "Camera mô hình / giả"),
    35: ("RED_LIGHT_CAMERA_ALT", "Camera đèn đỏ (khác)"),
    40: ("PHONE_CAMERA_ALT", "Camera dùng điện thoại"),
    41: ("DUMMY_CAMERA_ALT", "Camera mô hình"),
    42: ("SEATBELT_CAMERA_ALT", "Camera dây an toàn"),
    43: ("DISTANCE_CAMERA_ALT", "Camera khoảng cách"),
    44: ("BUS_LANE_CAMERA_ALT", "Camera làn buýt"),
    45: ("NOISE_CAMERA_ALT", "Camera tiếng ồn"),
    46: ("STOP_SIGN_CAMERA_ALT", "Camera dừng đỗ"),
    47: ("ANIMAL_ON_ROAD", "Động vật qua đường"),
    48: ("OBJECT_ON_ROAD", "Chướng ngại vật trên đường"),
    49: ("ROADKILL", "Xác động vật trên đường"),
    50: ("FLOOD", "Đường ngập nước"),
    51: ("FOG", "Sương mù"),
    52: ("HAIL", "Mưa đá"),
    53: ("SNOW", "Tuyết"),
    54: ("ICE", "Đóng băng"),
    55: ("SLIPPERY_ROAD", "Đường trơn trượt"),
    56: ("SPEED_BUMP", "Gờ giảm tốc"),
    57: ("SCHOOL_ZONE", "Khu vực trường học"),
    58: ("LANES_MERGING", "Nhập làn đường"),
    59: ("DANGEROUS_CURVES", "Khúc cua nguy hiểm"),
    60: ("FORK", "Nhánh rẽ phân tách"),
    61: ("BROKEN_TRAFFIC_LIGHT", "Đèn giao thông bị hỏng"),
    62: ("CYCLIST", "Người đi xe đạp"),
    63: ("EMERGENCY_VEHICLE", "Xe cứu hộ / ưu tiên"),
    64: ("PERSONAL_SAFETY", "Khu vực cảnh báo an ninh"),
    75: ("TRAFFIC_SIGNAL", "Đèn tín hiệu giao thông"),
}

# Nhóm cảnh báo phục vụ cảnh báo lái xe
CAMERA_TYPES = frozenset({3, 4, 23, 24, 25, 26, 27, 28, 29, 30, 31, 35,
                          40, 41, 42, 43, 44, 45, 46})
HAZARD_TYPES = frozenset({2, 5, 7, 11, 13, 14, 15, 16, 17, 18, 47, 48, 49,
                          50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
                          62, 63, 64})
SPEED_TYPES = frozenset({4, 8, 22, 24})
POLICE_TYPES = frozenset({1})


# ------------------------------------------------------------------ protobuf
def _varint(buf: bytes, i: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        byte = buf[i]
        i += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, i
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")


def _fields(buf: bytes, lo: int = 0, hi: int | None = None) -> dict:
    hi = len(buf) if hi is None else hi
    out: dict[int, list[tuple[int, object]]] = {}
    i = lo
    while i < hi:
        key, i = _varint(buf, i)
        if key == 0:
            break
        field, wire = key >> 3, key & 7
        if wire == 0:
            value, i = _varint(buf, i)
        elif wire == 2:
            length, i = _varint(buf, i)
            value = buf[i:i + length]
            i += length
        elif wire == 5:
            value = struct.unpack_from("<I", buf, i)[0]
            i += 4
        elif wire == 1:
            value = struct.unpack_from("<Q", buf, i)[0]
            i += 8
        else:
            raise ValueError(f"unsupported wire type {wire}")
        out.setdefault(field, []).append((wire, value))
    return out


def _zigzag(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


def parse_point_notices(plaintext: bytes) -> list[dict]:
    """Bóc danh sách cảnh báo điểm từ protobuf đã giải mã.

    Schema (đã xác minh trên 4513 bản ghi, 100% toạ độ nằm trong VN):
      top:  1=schema_version, 2=dataset_version, 3=built_at_ms, 4=spatial_zoom,
            5=repeated chunk
      chunk: 1=<int>, 2=<int>, 3=<packed notice records>
      record:1=id(str) 2=type(int) 3=lon_e6(sint32 zigzag)
             4=lat_e6(sint32 zigzag) 6=trigger_distance_m 9=side_rule
    """
    notices: list[dict] = []
    top = _fields(plaintext)
    for _, chunk in top.get(5, []):
        if not isinstance(chunk, (bytes, bytearray)):
            continue
        try:
            inner = _fields(chunk).get(3, [(2, b"")])[0][1]
        except Exception:
            continue
        if not isinstance(inner, (bytes, bytearray)):
            continue
        for start in range(len(inner) - 1):
            if inner[start] != 0x0A:      # field 1, wire 2 → bắt đầu record
                continue
            try:
                rec = _fields(inner, start, min(len(inner), start + 128))
                rid = rec[1][0][1]
                lon = _zigzag(rec[3][0][1]) / 1e6
                lat = _zigzag(rec[4][0][1]) / 1e6
            except Exception:
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            notices.append({
                "id": rid.decode("utf-8", "replace") if isinstance(rid, bytes) else str(rid),
                "type": rec[2][0][1] if 2 in rec else 0,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "trigger_m": rec[6][0][1] if 6 in rec else None,
                "side": rec[9][0][1] if 9 in rec else None,
            })
    return notices


# ------------------------------------------------------------------ tải mạng
def _fetch_sync(url: str) -> bytes:
    import ssl
    import urllib.request

    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": WAZE_UA})
    with urllib.request.urlopen(req, context=ctx, timeout=_HTTP_TIMEOUT) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        return resp.read(_DOWNLOAD_LIMIT)


async def _fetch(session, url: str) -> bytes:
    """Tải qua aiohttp nếu có session, nếu không thì chạy thread."""
    if session is not None:
        async with session.get(url, headers={"User-Agent": WAZE_UA},
                               timeout=_HTTP_TIMEOUT) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status} for {url}")
            return await resp.read()
    return await asyncio.to_thread(_fetch_sync, url)


def _decrypt(blob: bytes, manifest: dict) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    enc = manifest["encryption"]
    if enc.get("status") != "ENCRYPTED":
        raise RuntimeError(f"encryption status: {enc.get('status')}")
    nonce = base64.b64decode(enc["nonce"])
    tag = base64.b64decode(enc["authTag"])
    aad = enc["aad"].encode()
    plain = AESGCM(_AES_KEY).decrypt(nonce, blob + tag, aad)
    if manifest["payload"].get("compression") == "gzip":
        plain = gzip.decompress(plain)
    got = hashlib.sha256(plain).hexdigest()
    want = manifest["payload"]["checksum"]["value"]
    if got != want:
        raise RuntimeError("plaintext checksum mismatch")
    return plain


# ------------------------------------------------------------------ dataset
class WazeDataset:
    """Index cảnh báo điểm + truy vấn theo bán kính quanh xe."""

    def __init__(self, notices: list[dict], version: str = "", fetched_at: float = 0.0,
                 source: str = ""):
        self.notices = notices
        self.version = version
        self.fetched_at = fetched_at or time.time()
        self.source = source
        self._grid: dict[tuple[int, int], list[dict]] = {}
        self._cell = 0.01          # ~1.1 km
        for n in notices:
            self._grid.setdefault(
                (int(n["lat"] // self._cell), int(n["lon"] // self._cell)), []
            ).append(n)

    def __len__(self) -> int:
        return len(self.notices)

    def query(self, lat: float, lon: float, radius_m: float = 500.0,
              types: frozenset[int] | None = None, limit: int = 10) -> list[dict]:
        """Cảnh báo trong bán kính `radius_m`, sắp xếp gần nhất trước."""
        if lat is None or lon is None:
            return []
        span = int(math.ceil(radius_m / (self._cell * 111_320))) + 1
        cy, cx = int(lat // self._cell), int(lon // self._cell)
        out: list[dict] = []
        for dy in range(-span, span + 1):
            for dx in range(-span, span + 1):
                for n in self._grid.get((cy + dy, cx + dx), ()):
                    if types is not None and n["type"] not in types:
                        continue
                    d = haversine_m(lat, lon, n["lat"], n["lon"])
                    if d <= radius_m:
                        hit = dict(n)
                        hit["distance_m"] = round(d, 1)
                        out.append(hit)
        out.sort(key=lambda x: x["distance_m"])
        return out[:limit]


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def type_name(t: int) -> str:
    return ALERT_TYPES.get(t, (f"TYPE_{t}", f"Không rõ ({t})"))[1]


def type_code(t: int) -> str:
    return ALERT_TYPES.get(t, (f"TYPE_{t}", ""))[0]


async def async_load_dataset(session, cache_dir: str | Path,
                             force: bool = False) -> WazeDataset:
    """Tải/đọc cache dataset cảnh báo điểm. Chỉ tải mạng khi version đổi."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    meta_file = cache / "waze_meta.json"
    meta = {}
    if await asyncio.to_thread(meta_file.exists):
        try:
            meta = json.loads(await asyncio.to_thread(meta_file.read_text, "utf-8"))
        except Exception:
            meta = {}

    manifest = None
    last_error = None
    for base in (WAZE_BASE, WAZE_BASE_FALLBACK):
        try:
            manifest = json.loads((await _fetch(session, base + _POINT_MANIFEST)).decode())
            manifest["_base"] = base
            break
        except Exception as exc:                      # noqa: BLE001
            last_error = exc
    if manifest is None:
        raise RuntimeError(f"không lấy được manifest: {last_error}")

    version = str(manifest.get("version") or "")
    data_file = cache / f"waze_point_v{version}.json"
    if not force and version and await asyncio.to_thread(data_file.exists) \
            and meta.get("version") == version:
        try:
            notices = json.loads(await asyncio.to_thread(data_file.read_text, "utf-8"))
            return WazeDataset(notices, version,
                               (await asyncio.to_thread(data_file.stat)).st_mtime,
                               "cache")
        except Exception:
            pass

    blob = await _fetch(session, manifest["_base"] + manifest["artifact"]["url"])
    got = hashlib.sha256(blob).hexdigest()
    if got != manifest["checksum"]["value"]:
        raise RuntimeError("artifact checksum mismatch")
    plain = await asyncio.to_thread(_decrypt, blob, manifest)
    notices = await asyncio.to_thread(parse_point_notices, plain)

    tmp = data_file.with_suffix(".tmp")
    await asyncio.to_thread(tmp.write_text, json.dumps(notices, ensure_ascii=False), "utf-8")
    await asyncio.to_thread(tmp.replace, data_file)
    await asyncio.to_thread(meta_file.write_text, json.dumps({
        "version": version,
        "notices": len(notices),
        "fetched_at": time.time(),
        "base": manifest["_base"],
        "plaintext_sha256": manifest["payload"]["checksum"]["value"],
    }, ensure_ascii=False), "utf-8")
    for old in await asyncio.to_thread(lambda: list(cache.glob("waze_point_v*.json"))):
        if old.name != data_file.name:
            try:
                await asyncio.to_thread(old.unlink)
            except OSError:
                pass
    _LOGGER.info("Waze: nạp %d cảnh báo (version %s)", len(notices), version)
    return WazeDataset(notices, version, time.time(), "network")


if __name__ == "__main__":       # test offline
    import sys
    logging.basicConfig(level=logging.INFO)
    here = Path(__file__).parent

    async def _main() -> None:
        ds = await async_load_dataset(None, here / "cache", force="--force" in sys.argv)
        print(f"dataset: {len(ds)} cảnh báo, version={ds.version}, source={ds.source}")
        # toạ độ xe mẫu (Hà Giang, gần cảnh báo id 470317)
        for lat, lon in ((23.0621, 104.9917), (21.0278, 105.8342), (10.7769, 106.7009)):
            near = ds.query(lat, lon, 2000)
            print(f"\n({lat},{lon}) -> {len(near)} cảnh báo trong 2 km")
            for n in near[:3]:
                print(f"   {n['distance_m']:7.1f} m  {type_name(n['type'])}  id={n['id']}")

    asyncio.run(_main())
