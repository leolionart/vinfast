"""VinFast — lớp API chỉ-đọc mở rộng (dịch ngược từ ``base_1.apk``).

Bổ sung các endpoint mà app VinFast có nhưng component chưa dùng, phục vụ dashboard:
chẩn đoán/telltales, cảnh báo trộm, thông báo, Battery Care, điểm lái an toàn,
bảo hành, FOTA, thuê pin, ảnh vị trí đỗ, phiên bản T-Box.

Toàn bộ hàm ``parse_*`` là hàm thuần (nhận JSON, trả dict ``api_*``) nên kiểm thử
offline được; ``ExtendedApiClient`` chỉ lo gọi mạng.

Bằng chứng shape JSON: ``D:\\vinfast\\apk_re\\live_probe\\*.json`` và
``API_REFERENCE_FULL.md``.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping

from .api_helpers import safe_float

_LOGGER = logging.getLogger(__name__)

#: Endpoint (verb, path, cần X-VIN-CODE, tham số query)
PROFILE_PATH = "/ccarusermgnt/api/v1/auth0/account/profile"
WARRANTY_PATH = "/ccarusermgnt/api/v1/vehicle/warranty/{vin}"
DRIVERS_PATH = "/ccarusermgnt/api/v1/user-vehicle/driver"
TELLTALES_PATH = "/ccar-diagnostic/api/v1/c-app/telltales/alert-dashboard"
THIEF_PATH = "/notimgmt/api/v1/vehicles/{vin}/active-thief-warning"
NOTI_UNREAD_PATH = "/notimgmt/api/v1/notimgmt/users/app/is-unread"
BATTERY_INFO_PATH = "/vf-safety-driving/api/v1/capp/battery/info"
BATTERY_STATUS_PATH = "/vf-safety-driving/api/v1/capp/battery/status"
BATTERY_LAST_CHARGE_PATH = "/vf-safety-driving/api/v1/capp/battery/last-charge"
BATTERY_HABITS_PATH = "/vf-safety-driving/api/v1/capp/battery/{kind}-habits"
DRIVING_SCORE_PATH = "/vf-safety-driving/api/v1/driving-score"
FOTA_CHECK_PATH = "/ccarfota_v2/api/v1/campaigns/check-firmware-update/{vin}"
PARKED_IMAGES_PATH = "/ccaraccessmgmt/api/v1/vehicles/{vin}/parked-images"
CHARGING_CURRENT_PATH = "/ccarcharging/api/v1/charging-sessions/current"
BATTERY_LEASING_PATH = "/ccarcharging/api/v3/battery-leasing/info"
SOTA_PACKAGE_PATH = "/ccar-sota/api/v1/capp/package/v2/current-package"
#: [2.9.57] Ba endpoint mới, lấy từ capture app 2.26.11 (màn hình chủ).
NEXT_MAINTENANCE_PATH = "/ccarbookingservice/api/v1/c-app/next-maintenance"
RECALL_CAMPAIGNS_PATH = "/ccarbookingservice/api/v1/recall-campaigns/list"
VF_POINT_PATH = "/ccarreferral/api/v1/capp/vouchers/vf-point"

#: Mã thành công quan sát được: 200000 (đa số), 0 (fota/sota/thief).
OK_CODES = (200000, 0, 200, 201, 202, 204)


def _ok(body: Any) -> bool:
    if not isinstance(body, Mapping):
        return False
    code = body.get("code")
    if code is None:
        return True
    try:
        return int(code) in OK_CODES
    except (TypeError, ValueError):
        return False


def _data(body: Any) -> Any:
    if not isinstance(body, Mapping):
        return None
    return body.get("data")


def _json_or_none(value: Any) -> str | None:
    if value in (None, [], {}):
        return None
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return None


def _dict_data(body: Any) -> Mapping | None:
    """Trả ``data`` nếu là object không rỗng; ngược lại ``None``."""
    if not _ok(body):
        return None
    data = _data(body)
    if not isinstance(data, Mapping) or not data:
        return None
    return data


# ---------------------------------------------------------------------------
# Parsers (thuần, kiểm thử offline)
# ---------------------------------------------------------------------------

def parse_profile(body: Any) -> dict[str, Any]:
    """``GET /ccarusermgnt/api/v1/auth0/account/profile``."""
    data = _dict_data(body)
    if data is None:
        return {}
    return {
        "api_profile_name": data.get("name"),
        "api_profile_email": data.get("email"),
        "api_profile_phone": data.get("phoneNumber"),
        "api_profile_id": data.get("id"),
    }


def parse_warranty(body: Any) -> dict[str, Any]:
    """``GET /ccarusermgnt/api/v1/vehicle/warranty/{vin}``."""
    data = _dict_data(body)
    if data is None:
        return {}
    mileage = data.get("warrantyMileage")
    return {
        "api_warranty_end": (data.get("warrantyEndDate") or "")[:10] or None,
        "api_warranty_start": (data.get("warrantyStartDate") or "")[:10] or None,
        "api_warranty_years": data.get("yearsOfWarranty"),
        "api_warranty_mileage": safe_float(mileage, None) if mileage not in (None, "") else None,
    }


def parse_drivers(body: Any) -> dict[str, Any]:
    """``GET /ccarusermgnt/api/v1/user-vehicle/driver?vinCode=``."""
    data = _data(body)
    if not _ok(body):
        return {}
    if isinstance(data, list):
        drivers = data
    elif isinstance(data, Mapping):
        drivers = data.get("drivers") or data.get("content") or []
    else:
        drivers = []
    return {"api_drivers_count": len(drivers) if isinstance(drivers, list) else None}


def parse_telltales(body: Any) -> dict[str, Any]:
    """``GET /ccar-diagnostic/api/v1/c-app/telltales/alert-dashboard?vinCode=``.

    ``data`` là list ``{categoryName, categoryType, alertNo, alerts[]}``.
    """
    if not _ok(body):
        return {}
    data = _data(body)
    if not isinstance(data, list):
        return {"api_alert_count": 0}
    total = 0
    names = []
    for group in data:
        if not isinstance(group, Mapping):
            continue
        alerts = group.get("alerts") or []
        count = safe_float(group.get("alertNo"), 0) or 0
        count = max(count, len(alerts) if isinstance(alerts, list) else 0)
        if count:
            total += int(count)
        for alert in (alerts if isinstance(alerts, list) else []):
            if isinstance(alert, Mapping):
                title = alert.get("title") or alert.get("name") or alert.get("alertName")
                if title:
                    names.append(str(title))
    return {
        "api_alert_count": total,
        "api_alert_summary": "; ".join(names[:5]) if names else None,
        "api_alert_json": _json_or_none(data),
    }


def parse_thief_warning(body: Any) -> dict[str, Any]:
    """``GET /notimgmt/api/v1/vehicles/{vin}/active-thief-warning``.

    **Ngữ nghĩa quan trọng (đo thực tế 2026-09-17):** ``state`` là trạng thái
    **bật/tắt chuông báo trộm**, KHÔNG phải "đang bị trộm":
    xe VF3 của chủ tài khoản trả ``THEFT_ALERT_ACTIVATED`` (chuông đang bật),
    VF6 trả ``THEFT_ALERT_DEACTIVATED``. ``createdDate`` luôn bằng thời điểm gọi
    ⇒ đây là ảnh chụp trạng thái, không phải sự kiện.

    Sự kiện trộm thật nằm ở ``history`` (rỗng nghĩa là không có gì).
    """
    data = _dict_data(body)
    if data is None:
        return {}
    state = str(data.get("state") or "")
    armed = "ACTIVATED" in state.upper() and "DEACTIVATED" not in state.upper()
    history = data.get("history")
    has_event = bool(history) if isinstance(history, list) else False
    return {
        "api_thief_state": state or None,
        "api_thief_armed": armed,
        "api_thief_alert": has_event,
        "api_thief_message": (data.get("body") or data.get("tittle")) if has_event else None,
        "api_thief_time": data.get("createdDate") if has_event else None,
        "api_thief_lat": data.get("latestLatitude") if has_event else None,
        "api_thief_lon": data.get("latestLongitude") if has_event else None,
    }


def parse_noti_unread(body: Any) -> dict[str, Any]:
    """``GET /notimgmt/api/v1/notimgmt/users/app/is-unread`` — ``data`` là boolean."""
    if not _ok(body):
        return {}
    data = _data(body)
    if isinstance(data, Mapping):
        data = data.get("isUnread") or data.get("unread")
    return {"api_noti_unread": bool(data) if data is not None else None}


def parse_battery_info(body: Any) -> dict[str, Any]:
    data = _dict_data(body)
    if data is None:
        return {}
    return {"api_battery_brand": data.get("batteryBrand")}


def parse_battery_status(body: Any) -> dict[str, Any]:
    data = _dict_data(body)
    if data is None:
        return {}
    balance = data.get("cellBalanceStatus")
    return {
        "api_battery_cell_balance": balance,
        "api_battery_cell_balance_ok": (str(balance).upper() == "BALANCE") if balance else None,
        "api_battery_lv_status": data.get("lvBatteryStatus"),
    }


def _series_max(block: Any, field: str = "value") -> float | None:
    """Lấy giá trị LỚN NHẤT thật từ ``chartPoints``.

    Trường ``max`` của API là **trần trục đồ thị**, không phải giá trị thực — đo thật
    ngày 2026-09-17:

    * Một số VF3: ``batteryTemperature = {max: 100.0, chartPoints: []}``
      (không có điểm nào) và ``chargingPower = {max: 10.0, chartPoints: 80 điểm, đỉnh 2.912}``.
    * Một số VF6: ``batteryTemperature.max = 100.0`` nhưng đỉnh điểm là 33.0 °C;
      ``chargingPower.max = 90.0`` nhưng đỉnh điểm là 86.681 kW.

    Vì vậy ``max`` **không bao giờ** được dùng làm giá trị thực; không có điểm ⇒ không có dữ liệu
    (trả ``None`` để entity hiện ``unknown`` thay vì hiện trần trục).
    """
    if not isinstance(block, Mapping):
        return None
    points = block.get("chartPoints")
    if not isinstance(points, list):
        return None
    values = []
    for p in points:
        if isinstance(p, Mapping):
            try:
                values.append(float(p.get(field)))
            except (TypeError, ValueError):
                continue
    if not values:
        return None
    return max(values)


def _fmt_hours(ms: Any) -> str | None:
    """Đổi mili-giây thành chuỗi giờ cho dễ đọc."""
    try:
        total_min = float(ms) / 60000.0
    except (TypeError, ValueError):
        return None
    if total_min <= 0:
        return None
    if total_min < 60:
        return f"{total_min:.0f} phút"
    return f"{total_min / 60.0:.1f} giờ".replace(".0 giờ", " giờ")


def parse_battery_last_charge(body: Any) -> dict[str, Any]:
    """``GET /vf-safety-driving/api/v1/capp/battery/last-charge``."""
    data = _dict_data(body)
    if data is None:
        return {}
    power = data.get("chargingPower")
    temp = data.get("batteryTemperature")
    duration_ms = safe_float(data.get("duration"), 0) or 0
    # Chỉ lấy đỉnh THẬT từ chuỗi điểm — KHÔNG fallback về `max` vì đó là trần trục đồ thị
    # (VF3: `batteryTemperature = {max: 100.0, chartPoints: []}` ⇒ không có dữ liệu nhiệt độ).
    peak_power = _series_max(power)
    peak_temp = _series_max(temp)
    return {
        "api_last_charge_time": data.get("lastChargeTime"),
        "api_last_charge_type": data.get("chargingType"),
        "api_last_charge_status": data.get("status"),
        "api_last_charge_minutes": round(duration_ms / 60000.0, 1) if duration_ms else None,
        "api_last_charge_peak_power": round(peak_power, 1) if peak_power is not None else None,
        "api_last_charge_peak_temp": round(peak_temp, 1) if peak_temp is not None else None,
        "api_last_charge_temp_limit": safe_float(temp.get("threshold"), None) if isinstance(temp, Mapping) else None,
    }


def _habit_summary(kind: str, data: Mapping) -> str:
    """Biến JSON thói quen thành câu tiếng Việt đọc được."""
    if kind == "charging":
        total = data.get("totalSession")
        dc = data.get("totalChargingDC")
        ac = data.get("totalChargingAC")
        low = data.get("lowSoc")
        high = data.get("highSoc")
        n_low = data.get("totalChargingLowSoc")
        n_high = data.get("totalChargingHighSoc")
        parts = []
        if total:
            parts.append(f"{total} phiên (DC {dc if dc is not None else '?'}/AC {ac if ac is not None else '?'})")
        if n_low is not None and low is not None:
            parts.append(f"{n_low} lần sạc dưới {low:g}%")
        if n_high is not None and high is not None:
            parts.append(f"{n_high} lần sạc trên {high:g}%")
        return " · ".join(parts)

    if kind == "parking":
        below = _fmt_hours(data.get("batteryBelow"))
        above = _fmt_hours(data.get("batteryAbove"))
        hot = _fmt_hours(data.get("highAmbientTemp"))
        parts = []
        if below:
            parts.append(f"đỗ khi pin thấp {below}")
        if above:
            parts.append(f"đỗ khi pin cao {above}")
        if hot:
            parts.append(f"đỗ trời nóng {hot}")
        return " · ".join(parts)

    if kind == "driving":
        # API thật trả 2 nhóm: tăng tốc gấp và phanh gấp (mỗi nhóm có ngưỡng tuần/tháng).
        parts = []
        for label, key, week_key, month_key in (
            ("tăng tốc gấp", "harshAccelerationResult",
             "harshAccelerationThresholdWeek", "harshAccelerationThresholdMonth"),
            ("phanh gấp", "harshBrakingResult",
             "harshBrakingThresholdWeek", "harshBrakingThresholdMonth"),
        ):
            result = data.get(key)
            if not isinstance(result, Mapping):
                continue
            seg = []
            try:
                if result.get(week_key) is not None:
                    seg.append(f"tuần {float(result[week_key]):g}")
                if result.get(month_key) is not None:
                    seg.append(f"tháng {float(result[month_key]):g}")
            except (TypeError, ValueError):
                continue
            if seg:
                parts.append(f"{label}: {' / '.join(seg)}")
        accel = data.get("harshAccelerationResult")
        if isinstance(accel, Mapping) and accel.get("totalTime"):
            total_time = _fmt_hours(accel["totalTime"])
            if total_time:
                parts.append(f"tổng {total_time}")
        return " · ".join(parts)

    return ""


def parse_battery_habits(body: Any, kind: str) -> dict[str, Any]:
    """``GET /vf-safety-driving/api/v1/capp/battery/{kind}-habits?lastMonth=N``.

    Trả về **câu tóm tắt dễ đọc** thay vì JSON thô (JSON thô sẽ bị cắt ở 250 ký tự
    khi lên entity state).
    """
    if not _ok(body):
        return {}
    data = _data(body)
    key = f"api_battery_{kind}_habits"
    if not isinstance(data, Mapping) or not data:
        return {key: None}
    try:
        summary = _habit_summary(kind, data)
    except Exception:
        summary = ""
    return {key: summary or None}


def parse_driving_score(body: Any) -> dict[str, Any]:
    """``GET /vf-safety-driving/api/v1/driving-score?vinCode=``."""
    data = _dict_data(body)
    if data is None:
        return {}
    score = safe_float(data.get("score"), None)
    level = data.get("level")
    # API trả -1 khi chưa đủ dữ liệu chấm điểm (quan sát trên VF3 2026-09-17)
    if score is not None and score < 0:
        score = None
        level = None
    level_vn = {
        "SAFE": "An toàn",
        "NORMAL": "Bình thường",
        "WARNING": "Cần chú ý",
        "RISKY": "Rủi ro",
        "DANGER": "Nguy hiểm",
    }.get(str(level).upper(), level)
    return {
        "api_driving_score": round(score, 2) if score is not None else None,
        "api_driving_score_level": level_vn,
        "api_driving_score_period": data.get("id"),
        "api_driving_score_json": _json_or_none(data.get("indicators")),
    }


def parse_fota(body: Any) -> dict[str, Any]:
    """``GET /ccarfota_v2/api/v1/campaigns/check-firmware-update/{vin}``."""
    data = _dict_data(body)
    if data is None:
        return {}
    in_progress = data.get("inProgressFirmwareUpdate")
    succeeded = data.get("succeededFirmwareUpdate")
    return {
        "api_firmware_in_progress": _json_or_none(in_progress),
        "api_firmware_last_ok": _json_or_none(succeeded),
        "api_firmware_update_available": bool(in_progress),
    }


def parse_sota_package(body: Any) -> dict[str, Any]:
    """``GET /ccar-sota/api/v1/capp/package/v2/current-package?vinCode=``."""
    data = _dict_data(body)
    if data is None:
        return {}
    return {
        "api_tbox_version": data.get("tboxVersion"),
        "api_sota_package": data.get("packageId"),
        "api_sota_product": data.get("productCode"),
    }


def parse_next_maintenance(body: Any) -> dict[str, Any]:
    """``GET /ccarbookingservice/api/v1/c-app/next-maintenance``.

    Đo thật 2026-10-10 (VF6): ``nextMileage=90000``, ``unitDistance=Km``,
    ``nextDateMaintaince`` = epoch ms, kèm hai mốc tính theo ODO và theo thời gian.
    """
    data = _dict_data(body)
    if data is None:
        return {}
    raw_ms = data.get("nextDateMaintaince")
    iso = None
    try:
        if raw_ms:
            import datetime

            iso = datetime.datetime.fromtimestamp(
                int(raw_ms) / 1000, datetime.timezone.utc).isoformat()
    except (TypeError, ValueError):
        iso = None
    return {
        "api_next_maintenance_km": data.get("nextMileage"),
        "api_next_maintenance_unit": data.get("unitDistance"),
        "api_next_maintenance_date": iso,
        "api_next_maintenance_odo_date": data.get("nextDateMaintainceBasedOnOdo"),
        "api_next_maintenance_time_date": data.get("nextDateMaintainceBasedOnBU"),
    }


def parse_recall_campaigns(body: Any) -> dict[str, Any]:
    """``GET /ccarbookingservice/api/v1/recall-campaigns/list?vinCode=``.

    Lưu ý: endpoint này trả **500** khá thường xuyên (đo 2026-10-10), nên parser
    phải chịu được thiếu dữ liệu và không được làm hỏng các mục khác.
    """
    data = _dict_data(body)
    if data is None:
        return {}
    campaigns = data.get("campaigns")
    if campaigns is None:
        return {"api_recall_campaigns": None, "api_recall_count": None}
    if not isinstance(campaigns, list):
        return {"api_recall_campaigns": None, "api_recall_count": None}
    names = []
    for item in campaigns:
        if isinstance(item, Mapping):
            label = item.get("campaignName") or item.get("name") or item.get("campaignCode")
            if label:
                names.append(str(label))
    return {
        "api_recall_campaigns": ", ".join(names) if names else None,
        "api_recall_count": len(campaigns),
    }


def parse_vf_point(body: Any) -> dict[str, Any]:
    """``GET /ccarreferral/api/v1/capp/vouchers/vf-point`` — điểm VinClub/VF Point."""
    data = _dict_data(body)
    if data is None:
        return {}
    return {
        "api_vf_points": data.get("point"),
        "api_vinclub_joined": data.get("joined"),
        "api_vinclub_membership": data.get("membership"),
        "api_vinclub_code": data.get("membershipCode"),
    }


def parse_battery_leasing(body: Any) -> dict[str, Any]:
    """``GET /ccarcharging/api/v3/battery-leasing/info``."""
    data = _dict_data(body)
    if data is None:
        return {}
    target = data.get("targetSoc") or {}
    return {
        "api_leasing_cost": safe_float(data.get("cost"), None),
        "api_leasing_km": safe_float(data.get("actualKm"), None),
        "api_leasing_month": f"{data.get('month')}/{data.get('year')}" if data.get("month") else None,
        "api_leasing_odo_start": safe_float(data.get("initOdo"), None),
        "api_leasing_odo_end": safe_float(data.get("endOdo"), None),
        "api_leasing_target_soc": safe_float(target.get("target"), None) if isinstance(target, Mapping) else None,
        "api_leasing_free": bool(data.get("isFree")) if data.get("isFree") is not None else None,
    }


def parse_charging_current(body: Any) -> dict[str, Any]:
    """``GET /ccarcharging/api/v1/charging-sessions/current`` — list (thường rỗng)."""
    data = _data(body)
    if not _ok(body):
        return {}
    if isinstance(data, Mapping):
        data = data.get("content") or []
    if not isinstance(data, list):
        return {}
    if not data:
        return {"api_current_charging_session": None}
    session = data[0] if isinstance(data[0], Mapping) else {"raw": data[0]}
    return {"api_current_charging_session": _json_or_none(session)}


def parse_parked_images(body: Any) -> dict[str, Any]:
    """``GET /ccaraccessmgmt/api/v1/vehicles/{vin}/parked-images``."""
    if not _ok(body):
        return {}
    data = _data(body)
    if not data:
        return {"api_parked_images": None}
    urls: list[str] = []
    items = data if isinstance(data, list) else [data]
    for item in items:
        if isinstance(item, Mapping):
            for key in ("imageUrl", "url", "image", "parkedImage", "link"):
                if item.get(key):
                    urls.append(str(item[key]))
        elif isinstance(item, str):
            urls.append(item)
    return {"api_parked_images": _json_or_none(urls) if urls else _json_or_none(data)}


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ExtendedApiClient:
    """Gọi các endpoint chỉ-đọc mở rộng và trả về dict ``api_*`` để merge vào state."""

    def __init__(self, core):
        self.core = core

    async def _get(self, path: str, params: Mapping[str, Any] | None = None, vin: bool = False):
        auth = getattr(self.core, "auth", None)
        if auth is None:
            return None
        try:
            return await auth.api_request(
                "GET", path, params=dict(params or {}) or None, custom_vin=self.core.vin if vin else "none"
            )
        except Exception:
            _LOGGER.debug("VinFast: gọi %s thất bại", path, exc_info=True)
            return None

    @staticmethod
    def _json(res) -> Any:
        if res is None or getattr(res, "status_code", 0) != 200:
            return None
        try:
            return res.json()
        except Exception:
            return None

    async def refresh(self) -> dict[str, Any]:
        """Lấy toàn bộ dữ liệu mở rộng. Luôn trả dict (có thể rỗng), không ném lỗi."""
        vin = self.core.vin
        if not vin:
            return {}

        updates: dict[str, Any] = {}
        plan = [
            ("profile", PROFILE_PATH, None, False, parse_profile),
            ("warranty", WARRANTY_PATH.format(vin=vin), None, True, parse_warranty),
            ("drivers", DRIVERS_PATH, {"vinCode": vin}, False, parse_drivers),
            ("telltales", TELLTALES_PATH, {"vinCode": vin}, True, parse_telltales),
            ("thief", THIEF_PATH.format(vin=vin), None, True, parse_thief_warning),
            ("noti", NOTI_UNREAD_PATH, None, False, parse_noti_unread),
            ("battery_info", BATTERY_INFO_PATH, None, True, parse_battery_info),
            ("battery_status", BATTERY_STATUS_PATH, None, True, parse_battery_status),
            ("battery_last_charge", BATTERY_LAST_CHARGE_PATH, None, True, parse_battery_last_charge),
            ("driving_score", DRIVING_SCORE_PATH, {"vinCode": vin}, True, parse_driving_score),
            ("fota", FOTA_CHECK_PATH.format(vin=vin), None, True, parse_fota),
            ("sota", SOTA_PACKAGE_PATH, {"vinCode": vin}, True, parse_sota_package),
            ("leasing", BATTERY_LEASING_PATH, None, False, parse_battery_leasing),
            ("charging_current", CHARGING_CURRENT_PATH, None, False, parse_charging_current),
            ("parked_images", PARKED_IMAGES_PATH.format(vin=vin), None, True, parse_parked_images),
            # [2.9.57] Đồng bộ thêm 3 mục app 2.26.11 gọi ở màn hình chủ.
            ("next_maintenance", NEXT_MAINTENANCE_PATH, None, True, parse_next_maintenance),
            ("recall_campaigns", RECALL_CAMPAIGNS_PATH, {"vinCode": vin}, True, parse_recall_campaigns),
            ("vf_point", VF_POINT_PATH, None, False, parse_vf_point),
        ]

        for name, path, params, need_vin, parser in plan:
            body = self._json(await self._get(path, params, need_vin))
            if body is None:
                continue
            try:
                parsed = parser(body)
            except Exception:
                _LOGGER.debug("VinFast: parse %s lỗi", name, exc_info=True)
                continue
            # Ghi CẢ giá trị None: endpoint thành công nhưng thiếu trường nghĩa là
            # trường đó không còn dữ liệu — nếu lọc None thì state cũ sẽ tồn tại mãi.
            updates.update(parsed)

        # battery habits cần tham số lastMonth
        for kind in ("charging", "driving", "parking"):
            body = self._json(await self._get(BATTERY_HABITS_PATH.format(kind=kind), {"lastMonth": 3}, True))
            if body is None:
                continue
            try:
                updates.update(parse_battery_habits(body, kind))
            except Exception:
                _LOGGER.debug("VinFast: parse habits %s lỗi", kind, exc_info=True)

        return updates
