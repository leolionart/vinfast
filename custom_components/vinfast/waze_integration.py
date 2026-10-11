#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""waze_integration.py — gắn dữ liệu cảnh báo Waze Mod vào component VinFast.

Thiết kế (không sửa luồng MQTT của api.py):
  * Một task nền định kỳ đọc GPS xe từ `api._last_data` ("api_last_lat"/"api_last_lon").
  * Truy vấn dataset cảnh báo (đã tải + giải mã) theo bán kính quanh xe.
  * Ghi kết quả vào `api._last_data["api_waze_*"]` rồi gọi `api.trigger_callbacks()`
    để các sensor cập nhật — giống hệt cơ chế dữ liệu hiện có.
  * Bắn event `vinfast_waze_alert` khi có cảnh báo MỚI đi vào bán kính (chống trùng theo id).

Options (đọc từ entry.options, đều có mặc định nên KHÔNG cần sửa config_flow):
  waze_enabled        (bool,   True)
  waze_radius_m       (int,    500)
  waze_cameras_only   (bool,   False)  — chỉ cảnh báo nhóm camera
  waze_refresh_hours  (float,  6)
  waze_eval_seconds   (int,    20)
  waze_alert_cooldown_s (int,  300)    — không bắn lại cùng id trong khoảng này
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:                                     # chạy trong package HA
    from .waze_alerts import (
        CAMERA_TYPES,
        WazeDataset,
        async_load_dataset,
        haversine_m,
        type_name,
    )
except ImportError:                      # chạy standalone để test
    from waze_alerts import (            # type: ignore[no-redef]
        CAMERA_TYPES,
        WazeDataset,
        async_load_dataset,
        haversine_m,
        type_name,
    )

_LOGGER = logging.getLogger(__name__)

DOMAIN = "vinfast"
CACHE_DIR = "/home/pi/.homeassistant/waze_cache"
EVENT_WAZE_ALERT = "vinfast_waze_alert"

_GPS_KEYS = (("api_last_lat", "00006_00001_00000"),
             ("api_last_lon", "00006_00001_00001"))


def _opt(options: dict, key: str, default):
    value = (options or {}).get(key, default)
    if value in (None, ""):
        return default
    try:
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        if isinstance(default, float):
            return float(value)
        if isinstance(default, int):
            return int(float(value))
    except (TypeError, ValueError):
        return default
    return value


def _coord(data: dict, keys: tuple[str, str]):
    for key in keys:
        try:
            value = float(data.get(key))
        except (TypeError, ValueError):
            continue
        if keys[0].endswith("lat") and not -90 <= value <= 90:
            continue
        if keys[0].endswith("lon") and not -180 <= value <= 180:
            continue
        return value
    return None


def _fmt_distance(meters: float) -> str:
    if meters >= 1000:
        return f"{meters / 1000:.1f} km"
    return f"{int(round(meters))} m"


def evaluate(api, dataset: WazeDataset, options: dict,
             seen: dict[str, float]) -> str | None:
    """Tính cảnh báo quanh xe, ghi vào api._last_data. Trả tên cảnh báo đáng chú ý."""
    data = api._last_data
    lat = _coord(data, _GPS_KEYS[0])
    lon = _coord(data, _GPS_KEYS[1])
    radius = _opt(options, "waze_radius_m", 500)
    cameras_only = _opt(options, "waze_cameras_only", False)

    if lat is None or lon is None:
        data["api_waze_status"] = "Chưa có vị trí GPS"
        data["api_waze_nearest"] = None
        data["api_waze_nearest_m"] = None
        data["api_waze_nearby"] = None
        data["api_waze_camera_m"] = None
        return None

    found = dataset.query(lat, lon, radius, limit=25)
    if cameras_only:
        found = [n for n in found if n["type"] in CAMERA_TYPES]

    age_min = int((time.time() - dataset.fetched_at) / 60)
    data["api_waze_status"] = (
        f"{len(dataset)} cảnh báo · v{dataset.version} · {age_min} phút trước"
    )
    data["api_waze_nearby"] = len(found)
    data["api_waze_nearest"] = None
    data["api_waze_nearest_m"] = None
    data["api_waze_camera_m"] = None

    headline = None
    if found:
        first = found[0]
        name = type_name(first["type"])
        data["api_waze_nearest"] = f"{name} · {_fmt_distance(first['distance_m'])}"
        data["api_waze_nearest_m"] = first["distance_m"]
        headline = name
        cams = [n for n in found if n["type"] in CAMERA_TYPES]
        if cams:
            data["api_waze_camera_m"] = cams[0]["distance_m"]

    # ---- event cho cảnh báo MỚI (chống trùng theo id) ----
    cooldown = _opt(options, "waze_alert_cooldown_s", 300)
    now = time.time()
    for alert in found:
        aid = str(alert["id"])
        last = seen.get(aid)
        if last is not None and now - last < cooldown:
            continue
        seen[aid] = now
        try:
            api.hass.bus.async_fire(EVENT_WAZE_ALERT, {
                "vin": getattr(api, "vin", None),
                "id": aid,
                "type": alert["type"],
                "type_name": type_name(alert["type"]),
                "distance_m": alert["distance_m"],
                "lat": alert["lat"],
                "lon": alert["lon"],
                "trigger_m": alert.get("trigger_m"),
                "car_lat": lat,
                "car_lon": lon,
            })
        except Exception:                    # noqa: BLE001
            _LOGGER.debug("Waze: không bắn được event", exc_info=True)
        break            # chỉ bắn cảnh báo gần nhất mỗi vòng
    for aid in list(seen):
        if now - seen[aid] > 3600:
            seen.pop(aid, None)
    return headline


async def async_setup_waze(hass: HomeAssistant, entry, api) -> None:
    """Khởi động task nền; không chặn setup của integration."""
    options = dict(entry.options or {})
    if not _opt(options, "waze_enabled", True):
        _LOGGER.info("VinFast Waze: tắt qua option waze_enabled")
        return

    async def _runner() -> None:
        session = async_get_clientsession(hass)
        dataset: WazeDataset | None = None
        seen: dict[str, float] = {}
        last_load = 0.0
        refresh_s = max(600, int(_opt(options, "waze_refresh_hours", 6) * 3600))
        eval_s = max(5, _opt(options, "waze_eval_seconds", 20))
        while True:
            try:
                if dataset is None or time.time() - last_load > refresh_s:
                    dataset = await async_load_dataset(session, CACHE_DIR)
                    last_load = time.time()
                evaluate(api, dataset, options, seen)
                api.trigger_callbacks()
            except asyncio.CancelledError:
                raise
            except Exception as exc:         # noqa: BLE001
                _LOGGER.warning("VinFast Waze: lỗi vòng lặp (%s: %s)",
                                type(exc).__name__, exc)
                try:
                    api._last_data["api_waze_status"] = f"Lỗi: {type(exc).__name__}"
                    api.trigger_callbacks()
                except Exception:            # noqa: BLE001
                    pass
            await asyncio.sleep(eval_s)

    task = hass.async_create_task(_runner(), name=f"vinfast_waze_{entry.entry_id}")
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})["waze_task"] = task
    _LOGGER.info("VinFast Waze: đã khởi động task cảnh báo theo toạ độ")
