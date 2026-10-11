"""Lossless raw GPS storage. Coordinates are never transformed or dropped."""
import os, json, math, time, tempfile, threading
import logging

_LOGGER = logging.getLogger(__name__)


def _valid(lat, lon):
    try:
        return math.isfinite(float(lat)) and math.isfinite(float(lon)) and -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180 and (float(lat) != 0 or float(lon) != 0)
    except (TypeError, ValueError):
        return False


def _read(path, default, *, allow_missing=True):
    if not os.path.exists(path):
        if allow_missing:
            return default
        raise FileNotFoundError(path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("points"), list):
            raise ValueError("invalid GPS storage schema")
        return data
    except Exception:
        _LOGGER.exception("VinFast: raw GPS file unreadable; refusing overwrite: %s", path)
        raise


def _atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class TripStorageManager:
    SCHEMA_VERSION = 2

    def __init__(self, storage_dir, vin):
        self.vin = vin.upper()
        self.directory = os.path.join(storage_dir, "vinfast_trips", vin.lower())
        os.makedirs(self.directory, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, date):
        return os.path.join(self.directory, f"trip_raw_{date}.json")

    async def async_append_point(self, hass, lat, lon, speed_kmh, heading, timestamp_ms, trip_id, trip_active, date_str, source="mqtt"):
        if not _valid(lat, lon):
            # [2.9.54] WARNING -> DEBUG: GPS rác từ xe là chuyện thường, đã bị chặn ở đây.
            _LOGGER.debug("VinFast: rejected invalid GPS fix lat=%r lon=%r", lat, lon)
            return False
        try:
            speed = float(speed_kmh)
        except (TypeError, ValueError):
            speed = 0.0
        try:
            heading = float(heading)
        except (TypeError, ValueError):
            heading = 0.0
        point = {
            "timestamp_ms": int(timestamp_ms or time.time() * 1000),
            "lat": float(lat), "lon": float(lon),
            "speed_kmh": speed, "heading": heading,
            "trip_id": trip_id, "trip_active": bool(trip_active), "source": source,
        }
        try:
            await hass.async_add_executor_job(self._append, point, date_str)
            return True
        except Exception as e:
            _LOGGER.error("VinFast: [RAW-APPEND] Ghi raw thất bại: %s", e)
            raise

    def _append(self, point, date):
        with self._lock:
            path = self._path(date)
            default = {"schema_version": self.SCHEMA_VERSION, "vin": self.vin, "date": date, "mode": "raw", "generated_at_ms": int(time.time() * 1000), "points": []}
            raw = _read(path, default)
            points = raw["points"]
            last_seq = max((int(p.get("seq", 0)) for p in points if isinstance(p, dict)), default=0)
            rec = {"seq": last_seq + 1, **point}
            points.append(rec)
            raw["schema_version"] = self.SCHEMA_VERSION
            raw["generated_at_ms"] = int(time.time() * 1000)
            _atomic(path, raw)

    def load_day(self, date, mode="raw"):
        # `smooth` remains a compatibility alias. It never transforms data.
        data = _read(self._path(date), {"schema_version": self.SCHEMA_VERSION, "vin": self.vin, "date": date, "mode": "raw", "points": []})
        data["mode"] = "raw"
        data["transform"] = "none"
        return data
