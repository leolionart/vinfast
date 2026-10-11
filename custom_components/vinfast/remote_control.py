"""VinFast remote-control protocol — lớp gửi lệnh điều khiển xe (API v2).

Toàn bộ hằng số, tên trường và thuật toán trong file này được dịch ngược trực tiếp
từ ``base_1.apk`` (package ``com.vinfast.companion.remotecontrolskit``). Xem
``DIEU_KHIEN_REMOTE_CONTROL.md`` ở gốc repo để có bằng chứng và bảng đối chiếu.

Module này **không** import Home Assistant để có thể kiểm thử offline.

Điểm quan trọng nhất: endpoint điều khiển **bắt buộc** có ``signature``
(RSA-SHA256 bằng khoá thiết bị sinh lúc pairing). Thiếu khoá thì phải dừng lại
(fail-closed) chứ không được gửi body thiếu chữ ký.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

_LOGGER = logging.getLogger(__name__)

#: Endpoint thật, lấy từ annotation ``@retrofit2.http.POST`` của ``RemoteApi.b``.
REMOTE_COMMAND_PATH = "/ccaraccessmgmt/api/v2/remote/app/command"
#: Endpoint v3 (MQTT-over-REST) của ``RemoteApi.c`` — chưa dùng, ghi lại để tham chiếu.
REMOTE_COMMAND_PATH_V3 = "/ccaraccessmgmt/api/v3/remote/app/command"

MESSAGE_NAME_REMOTE_CONTROL = "REMOTE_CONTROL"
MESSAGE_NAME_TEST_COMMAND = "TEST_COMMAND"

#: ``RemoteControlManager.s()`` trả về khoảng chênh cấu hình cho ``wakeUpTimeOut``.
#: Giá trị thật đọc từ remote config của app; HA dùng mặc định 30 giây.
DEFAULT_WAKEUP_TIMEOUT_MS = 30_000

#: Các dòng xe dùng cốp điện (``{"trunk":"OPEN"}``) thay vì mở khoá cốp
#: (``{"trunk":"UNLOCK"}``). Suy ra từ ``RemoteControlHelper.b`` trong APK.
_POWER_TAILGATE_MODELS = ("VF7", "VF8", "VF8NP", "VF9", "LAC HONG 900", "LACHONG900")


#: Mã lỗi quan sát được từ server khi probe thật (2026-09-17).
KNOWN_ERROR_CODES: dict[int, str] = {
    262150: (
        "Sending sms failed — tài khoản/xe chưa hoàn tất kích hoạt điều khiển từ xa; "
        "server đòi bước xác thực SMS/OTP trước khi nhận lệnh."
    ),
    131084: (
        "Not found session — sessionId (ssid) không tồn tại; phải quét QR thật "
        "trên màn hình xe mới có phiên pairing hợp lệ."
    ),
}

#: Bảng mã lỗi của app (``MessageError`` trong classes4.dex), giải mã từ bytecode.
#: Mã = **giá trị nhóm OR offset**:
#:   ``C_SUCCESS_CODE = 0`` · ``C_SYSTEM_ERROR_CODE = 65536 (0x10000)`` ·
#:   ``C_UDS_ERROR_CODE = 262144 (0x40000)``.
#: Hai mã đặc biệt ``0xFFFFFFFF`` / ``0xFFFFFFFD`` là sentinel (không thuộc nhóm nào).
MESSAGE_ERROR_GROUPS: dict[str, int] = {
    "C_SUCCESS_CODE": 0,
    "C_SYSTEM_ERROR_CODE": 0x10000,
    "C_UDS_ERROR_CODE": 0x40000,
}

MESSAGE_ERROR_CODES: dict[int, str] = {
    0: "C_COMPLETED_SUCCESSFULLY — lệnh đã thực thi xong",
    1: "C_PROCESSING — xe đang xử lý",
    2: "C_WAITING — đang chờ xe phản hồi",
    0x10001: "C_UNAUTHORIZED — không có quyền với xe/session này",
    0x10002: "C_TIMEOUT — hết thời gian chờ xe",
    0x10006: "C_FAILED_PARSE — server không phân tích được nội dung lệnh",
    0x40001: "C_UDS_PRECONDITION_FAILED — xe không thoả điều kiện thực thi (UDS)",
    0x40002: "C_UDS_USER_DENIED — người dùng trên xe từ chối",
    0x40003: "C_UDS_USER_STOPPED — người dùng trên xe dừng giữa chừng",
    0x40004: "C_SESSION_NOT_FOUND — không tìm thấy phiên điều khiển",
    0x40005: "C_SIGNATURE_VERIFY_FAILURE — chữ ký không hợp lệ (sai khoá pairing)",
    0x40007: "C_FAILED_PARSE_SECOND — giải mã lần hai thất bại",
    0x40008: "C_FAILED_ENCRYPTED — dữ liệu mã hoá sai/không giải mã được",
    0x40009: "C_SESSION_EXPIRED — phiên điều khiển đã hết hạn",
    0xFFFFFFFF: "C_NOT_IMPLEMENTED — xe không hỗ trợ lệnh này",
    0xFFFFFFFD: "C_INVALID — lệnh/dữ liệu không hợp lệ",
}


def explain_error_code(code: Any) -> str | None:
    """Diễn giải mã lỗi đã gặp khi kiểm thử thật, sau đó tới bảng mã của app."""
    try:
        value = int(code)
    except (TypeError, ValueError):
        return None
    if value in KNOWN_ERROR_CODES:
        return KNOWN_ERROR_CODES[value]
    return MESSAGE_ERROR_CODES.get(value)


class RemoteControlError(Exception):
    """Lỗi cấu hình hoặc lỗi dựng lệnh điều khiển (fail-closed)."""


# ---------------------------------------------------------------------------
# Tiện ích mã hoá — tương ứng SecurityUtils trong APK
# ---------------------------------------------------------------------------

def encode_base64_no_wrap(raw: bytes) -> str:
    """``SecurityUtils.j`` — Base64 NO_WRAP."""
    return base64.b64encode(raw).decode("ascii")


def decode_base64_no_wrap(encoded: str) -> bytes:
    """``SecurityUtils.h`` — Base64 decode NO_WRAP."""
    return base64.b64decode(encoded)


def sha256_digest(raw: bytes) -> bytes:
    """``SecurityUtils.o`` — SHA-256."""
    return hashlib.sha256(raw).digest()


def hmac_sha256(key: bytes, chunks: list[bytes]) -> bytes:
    """``SecurityUtils.n`` — HMAC-SHA256 trên các mảng nối tiếp."""
    mac = hmac.new(key, digestmod=hashlib.sha256)
    for chunk in chunks:
        mac.update(chunk)
    return mac.digest()


def load_private_key(pem: str) -> rsa.RSAPrivateKey:
    """``SecurityUtils.d`` — nạp khoá riêng từ PEM."""
    try:
        key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    except Exception as exc:  # noqa: BLE001 - thông báo cho người dùng
        raise RemoteControlError(f"Không đọc được khoá riêng điều khiển (PEM không hợp lệ): {exc}") from exc
    if not isinstance(key, rsa.RSAPrivateKey):
        raise RemoteControlError("Khoá điều khiển phải là khoá RSA.")
    return key


def rsa_sign_base64(private_key: rsa.RSAPrivateKey, chunks: list[bytes]) -> str:
    """``SecurityUtils.q`` — SHA256withRSA trên các mảng nối tiếp, trả Base64 NO_WRAP."""
    signer = private_key.sign(b"".join(chunks), padding.PKCS1v15(), hashes.SHA256())
    return encode_base64_no_wrap(signer)


def serialize_private_key_pem(key: Any) -> str:
    """Chuyển object khoá đã nạp sẵn của component thành PEM PKCS#8 (không mã hoá).

    Dùng để tái sử dụng chính khoá RSA mà component đã nạp cho X-HASH làm khoá ký
    lệnh điều khiển, thay vì bắt người dùng nhập lại PEM.
    """
    if key is None:
        return ""
    if not isinstance(key, rsa.RSAPrivateKey):
        raise RemoteControlError("Khoá điều khiển phải là khoá RSA.")
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def user_id_hash(user_id: str) -> str:
    """``Base64NoWrap(SHA256(userId))`` — đúng như app dựng field ``user_id``."""
    return encode_base64_no_wrap(sha256_digest(user_id.encode("utf-8")))


# ---------------------------------------------------------------------------
# Danh mục lệnh
# ---------------------------------------------------------------------------

def _compact(payload: Mapping[str, Any]) -> str:
    """Gson mặc định bỏ field null và không thêm khoảng trắng."""
    clean = {k: v for k, v in payload.items() if v is not None}
    return json.dumps(clean, separators=(",", ":"), ensure_ascii=False)


def _doors(state: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({"doors": state})


def _flat(key: str, state: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({key: state})


def _climate(field: str, state: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({field: state})


def _climate_driver_temp(params: Mapping[str, Any]) -> str:
    temperature = params.get("temperature", params.get("target_temp"))
    if temperature is None:
        raise RemoteControlError("Lệnh đặt nhiệt độ cần tham số 'temperature'.")
    try:
        value = float(temperature)
    except (TypeError, ValueError) as exc:
        raise RemoteControlError(f"Nhiệt độ không hợp lệ: {temperature!r}") from exc
    if not 15.0 <= value <= 32.0:
        raise RemoteControlError(f"Nhiệt độ ngoài khoảng cho phép 15–32 °C: {value}")
    return _compact({"set_driver_temperature": round(value, 1)})


def _charging(state: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({"charging_control": state})


def _model_key(model_display: str | None) -> str:
    if not model_display:
        return ""
    return str(model_display).upper().replace("_", " ").replace("-", " ").strip()


def _has_power_tailgate(model_display: str | None, is_eco: bool = False) -> bool:
    """``RemoteControlHelper.b``: VF7/VF8/VF8NP/VF9/LacHong900 (không phải Eco) → cốp điện."""
    if is_eco:
        return False
    normalised = _model_key(model_display)
    compact = normalised.replace(" ", "")
    for candidate in _POWER_TAILGATE_MODELS:
        if compact == candidate.replace(" ", ""):
            return True
    return False


@dataclass(frozen=True)
class RemoteCommand:
    """Một lệnh điều khiển.

    ``command_id`` giữ nguyên dải số 1..7 của ``bridge_contract.md`` để không phá
    entity id mà thẻ Lovelace đang gọi trực tiếp.
    """

    command_id: int
    slug: str
    name: str
    icon: str
    use_case: str
    build_content: Callable[[Mapping[str, Any]], str]
    message_name: str = MESSAGE_NAME_REMOTE_CONTROL
    tag: str | None = None


def _trunk_open(params: Mapping[str, Any]) -> str:
    mode = str(params.get("trunk_open_mode", "")).upper()
    if mode == "OPEN":
        return _compact({"trunk": "OPEN"})
    if mode == "UNLOCK":
        return _compact({"trunk": "UNLOCK"})
    model = params.get("vehicle_model")
    is_eco = bool(params.get("is_eco_variant"))
    return _compact({"trunk": "OPEN" if _has_power_tailgate(model, is_eco) else "UNLOCK"})


COMMANDS: dict[int, RemoteCommand] = {
    1: RemoteCommand(1, "khoa_cua", "Khóa cửa", "mdi:lock", "DoorsLock", _doors("LOCK")),
    2: RemoteCommand(2, "mo_cua", "Mở cửa", "mdi:lock-open", "DoorsUnlock", _doors("UNLOCK")),
    3: RemoteCommand(3, "bam_coi", "Bấm còi", "mdi:bullhorn", "HornOn", _flat("horn", "ON")),
    4: RemoteCommand(4, "nhay_den", "Nháy đèn", "mdi:car-light-high", "Flashing", _flat("headlight", "FLASHING")),
    5: RemoteCommand(5, "bat_dieu_hoa", "Bật điều hòa", "mdi:fan", "ClimateACOn", _climate("air_condition_enable", "ON")),
    6: RemoteCommand(6, "tat_dieu_hoa", "Tắt điều hòa", "mdi:fan-off", "ClimateACOff", _climate("air_condition_enable", "OFF")),
    7: RemoteCommand(7, "mo_cop", "Mở cốp", "mdi:car-back", "TrunkOpen", _trunk_open),
    8: RemoteCommand(8, "dong_cop", "Đóng cốp", "mdi:car-back", "TrunkClose", _flat("trunk", "CLOSE")),
    9: RemoteCommand(9, "tat_den", "Tắt nháy đèn", "mdi:car-light-dimmed", "FlashOff", _flat("headlight", "OFF")),
    10: RemoteCommand(10, "tat_coi", "Tắt còi", "mdi:bullhorn-outline", "HornOff", _flat("horn", "OFF")),
    11: RemoteCommand(11, "mo_kinh", "Mở cửa sổ", "mdi:car-window", "WindowsOpen", _flat("windows", "OPEN")),
    12: RemoteCommand(12, "dong_kinh", "Đóng cửa sổ", "mdi:car-window", "WindowsClose", _flat("windows", "CLOSE")),
    13: RemoteCommand(13, "mo_nap_sac", "Mở nắp sạc", "mdi:ev-plug-type2", "LidOpen", _flat("chargeport", "UNLOCK")),
    14: RemoteCommand(14, "bat_camp_mode", "Bật Camp Mode", "mdi:tent", "CampModeActive", _flat("campmode", "ACTIVE")),
    15: RemoteCommand(15, "tat_camp_mode", "Tắt Camp Mode", "mdi:tent", "CampModeDeactive", _flat("campmode", "DEACTIVE")),
    16: RemoteCommand(16, "bat_pet_mode", "Bật Pet Mode", "mdi:dog", "PetModeActive", _flat("petmode", "ACTIVE")),
    17: RemoteCommand(17, "tat_pet_mode", "Tắt Pet Mode", "mdi:dog", "PetModeDeactive", _flat("petmode", "DEACTIVE")),
    18: RemoteCommand(18, "bat_valet_mode", "Bật Valet Mode", "mdi:account-key", "ValetModeActive", _flat("valetmode", "ACTIVE")),
    19: RemoteCommand(19, "tat_valet_mode", "Tắt Valet Mode", "mdi:account-key", "ValetModeDeactive", _flat("valetmode", "DEACTIVE")),
    20: RemoteCommand(20, "bat_sac", "Bắt đầu sạc", "mdi:battery-charging", "ChargingStart", _charging("START_CHARGING_NOW")),
    21: RemoteCommand(21, "dung_sac", "Dừng sạc", "mdi:battery-off", "ChargingStop", _charging("STOP_CHARGING_NOW")),
    22: RemoteCommand(22, "dat_nhiet_do_lai", "Đặt nhiệt độ ghế lái", "mdi:thermometer", "ClimateDriverTemp", _climate_driver_temp),
}

COMMAND_BY_SLUG: dict[str, RemoteCommand] = {c.slug: c for c in COMMANDS.values()}
COMMAND_BY_USE_CASE: dict[str, RemoteCommand] = {c.use_case: c for c in COMMANDS.values()}

# ---------------------------------------------------------------------------
# DANH MỤC MỞ RỘNG — 75 use case thật của APK 2.25.7
# ---------------------------------------------------------------------------
# Nguồn: 75 lớp `RemoteItemUseCases$*` trong
# ``com/vinfast/companion/remotecontrolskit/persitent/model/info/common/`` (classes6.dex)
# + khoá wire `@SerializedName` của các DTO `mqttkit/domain/remotecontrol/common/raw/*`.
# Danh sách đầy đủ và bằng chứng: `APK_HIDDEN_CODES.md`.
#
# Các lệnh dưới đây KHÔNG tạo nút trên HA theo mặc định (tránh ~30 nút mới);
# bật bằng tuỳ chọn `control_advanced_buttons`. Vẫn gọi được qua service
# `button.press`/`api.send_remote_command(<slug>)` như bình thường.

#: Giá trị enum hợp lệ trên wire (đọc từ `<clinit>` của enum trong classes4.dex).
FAN_LEVELS: tuple[str, ...] = ("OFF", "LEVEL1", "LEVEL2", "LEVEL3", "LEVEL4",
                               "LEVEL5", "LEVEL6", "LEVEL7", "LEVEL8")
RECIRCULATION: tuple[str, ...] = ("INTER", "OUTER")
AIR_FLOW_DIRECTION: tuple[str, ...] = ("OFF", "VENT", "FOOT", "VENT_FOOT")
FLAP_POSITION: tuple[str, ...] = (
    "OFF", "FACE", "FOOT", "FOOT_FACE", "FOOT_WINDOW", "VENT", "VENT_FOOT",
    "DEFROST", "FOOT_DEFROST", "VENT_DEFROST", "FOOT_VENT_DEFROST",
)
DOWNLOAD_CONTROL: tuple[str, ...] = ("START_DOWNLOAD", "PAUSE_DOWNLOAD", "RESUME_DOWNLOAD", "CANCEL_DOWNLOAD")
SCHEDULE_FOTA: tuple[str, ...] = ("SET_SCHEDULE", "SET_RESCHEDULE", "POSTPONE_SCHEDULE")
CHARGING_CONTROL: tuple[str, ...] = ("NO_REQUEST", "START_CHARGING_NOW", "STOP_CHARGING_NOW")
CHARGE_SCHEDULE_MODE: tuple[str, ...] = ("NONE", "CHARGE_IN_PEAK_OFF_TIME_ONLY")
CLIMATE_TIMER: tuple[str, ...] = ("TURN_ON_SCHEDULE", "TURN_OFF_SCHEDULE")


def _enum_param(params: Mapping[str, Any], key: str, allowed: tuple[str, ...], default: str | None = None) -> str:
    raw = params.get(key, default)
    if raw is None:
        raise RemoteControlError(f"Lệnh này cần tham số '{key}' (một trong: {', '.join(allowed)}).")
    value = str(raw).upper().replace(" ", "_")
    if value not in allowed:
        raise RemoteControlError(f"'{key}' không hợp lệ: {raw!r}. Chỉ nhận: {', '.join(allowed)}.")
    return value


def _float_param(params: Mapping[str, Any], keys: tuple[str, ...], low: float, high: float) -> float:
    for key in keys:
        if params.get(key) is not None:
            raw = params[key]
            break
    else:
        raise RemoteControlError(f"Lệnh này cần tham số nhiệt độ ({keys[0]}).")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise RemoteControlError(f"Nhiệt độ không hợp lệ: {raw!r}") from exc
    if not low <= value <= high:
        raise RemoteControlError(f"Nhiệt độ ngoài khoảng cho phép {low:g}–{high:g} °C: {value}")
    return round(value, 1)


def _int_param(params: Mapping[str, Any], key: str, low: int, high: int, default: int | None = None) -> int:
    raw = params.get(key, default)
    if raw is None:
        raise RemoteControlError(f"Lệnh này cần tham số '{key}'.")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise RemoteControlError(f"'{key}' không hợp lệ: {raw!r}") from exc
    if not low <= value <= high:
        raise RemoteControlError(f"'{key}' ngoài khoảng {low}–{high}: {value}")
    return value


# --- builders cho từng nhóm lệnh mới --------------------------------------

def _climate_fan_speed(params: Mapping[str, Any]) -> str:
    return _compact({"set_fan_speed": _enum_param(params, "fan_speed", FAN_LEVELS)})


def _climate_passenger_temp(params: Mapping[str, Any]) -> str:
    value = _float_param(params, ("temperature", "target_temp", "passenger_temperature"), 15.0, 32.0)
    return _compact({"set_passenger_temperature": value})


def _climate_recirculation(state: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({"set_recirculation": state})


def _target_soc(params: Mapping[str, Any]) -> str:
    soc = _int_param(params, "target_soc", 50, 100)
    payload: dict[str, Any] = {"target_soc": soc}
    control = params.get("charging_control")
    if control is not None:
        payload["charging_control"] = _enum_param(params, "charging_control", CHARGING_CONTROL)
    return _compact(payload)


def _charge_schedule_set(params: Mapping[str, Any]) -> str:
    start = _int_param(params, "peak_off_hour_start", 0, 23, default=0)
    end = _int_param(params, "peak_off_hour_end", 0, 23, default=0)
    mode = _enum_param(params, "charge_schedule_mode", CHARGE_SCHEDULE_MODE,
                       default="CHARGE_IN_PEAK_OFF_TIME_ONLY")
    return _compact({
        "charge_schedule_mode": mode,
        "peak_off_hour_start": start,
        "peak_off_hour_end": end,
        "repeat_schedule": bool(params.get("repeat_schedule", True)),
    })


def _charge_schedule_cancel(_params: Mapping[str, Any]) -> str:
    return _compact({"charge_schedule_mode": "NONE"})


def _climate_schedule(timer: str) -> Callable[[Mapping[str, Any]], str]:
    def build(params: Mapping[str, Any]) -> str:
        payload: dict[str, Any] = {"climate_timer": timer}
        if params.get("departure_time"):
            payload["departure_time"] = str(params["departure_time"])
        if params.get("driver_temperature") is not None or params.get("temperature") is not None:
            payload["set_driver_temperature"] = _float_param(
                params, ("driver_temperature", "temperature"), 15.0, 32.0)
        if params.get("passenger_temperature") is not None:
            payload["set_passenger_temperature"] = _float_param(
                params, ("passenger_temperature",), 15.0, 32.0)
        if params.get("fan_speed") is not None:
            payload["set_fan_speed"] = _enum_param(params, "fan_speed", FAN_LEVELS)
        if params.get("precondition_duration") is not None:
            payload["precondition_duration"] = _int_param(params, "precondition_duration", 1, 60)
        if params.get("timezone"):
            payload["timezone"] = str(params["timezone"])
        return _compact(payload)
    return build


def _fota_download(state: str) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({"download_control": state})


def _fota_install_now(_params: Mapping[str, Any]) -> str:
    return _compact({"install_now": True})


def _fota_auto_download(enabled: bool) -> Callable[[Mapping[str, Any]], str]:
    return lambda _params: _compact({"setting_auto_download": enabled})


def _fota_download_config(params: Mapping[str, Any]) -> str:
    return _compact({"setting_download_over_lte": bool(params.get("download_over_lte", False))})


def _fota_schedule(params: Mapping[str, Any]) -> str:
    payload: dict[str, Any] = {"schedule_fota": _enum_param(params, "schedule_fota", SCHEDULE_FOTA,
                                                            default="SET_SCHEDULE")}
    if params.get("schedule_time") is not None:
        payload["schedule_time"] = _int_param(params, "schedule_time", 0, 2_000_000_000)
    return _compact(payload)


#: Lệnh mở rộng: id 101+ để không đụng dải 1..22 (giữ nguyên entity id cũ).
EXTRA_COMMANDS: dict[int, RemoteCommand] = {
    101: RemoteCommand(101, "mo_capo", "Mở capo (frunk)", "mdi:car-door", "HoodOpen", _flat("frunk", "UNLOCK")),
    102: RemoteCommand(102, "dong_capo", "Đóng capo", "mdi:car-door", "HoodClose", _flat("frunk", "CLOSE")),
    103: RemoteCommand(103, "mo_cua_so_troi", "Mở cửa sổ trời", "mdi:weather-sunny", "SunRoofOpen", _flat("sunroof", "OPEN")),
    104: RemoteCommand(104, "dong_cua_so_troi", "Đóng cửa sổ trời", "mdi:weather-sunset", "SunRoofClose", _flat("sunroof", "CLOSE")),
    105: RemoteCommand(105, "khoa_nap_sac", "Khoá nắp sạc", "mdi:ev-plug-type2", "LidClose", _flat("chargeport", "LOCK")),
    106: RemoteCommand(106, "dat_soc_muc_tieu", "Đặt SOC mục tiêu", "mdi:battery-sync", "TargetSOC", _target_soc),
    107: RemoteCommand(107, "dat_gio_sac_uu_tien", "Đặt giờ sạc ưu tiên", "mdi:clock-start", "ChargingStatusSetSchedule", _charge_schedule_set),
    108: RemoteCommand(108, "huy_gio_sac", "Huỷ lịch sạc", "mdi:calendar-remove", "ChargingStatusCancelScheduling", _charge_schedule_cancel),
    109: RemoteCommand(109, "sac_khong_yeu_cau", "Sạc: không yêu cầu", "mdi:battery-sync-outline", "ChargingStatusNoRequest", _charging("NO_REQUEST")),
    110: RemoteCommand(110, "dat_toc_do_quat", "Đặt tốc độ quạt", "mdi:fan-speed-3", "ClimateFanSpeed", _climate_fan_speed),
    111: RemoteCommand(111, "bat_auto_ac", "Bật Auto AC", "mdi:air-conditioner", "ClimateAutoACOn", _climate("enable_auto_ac", "ON")),
    112: RemoteCommand(112, "tat_auto_ac", "Tắt Auto AC", "mdi:air-conditioner", "ClimateAutoACOff", _climate("enable_auto_ac", "OFF")),
    113: RemoteCommand(113, "bat_max_ac", "Bật Max AC", "mdi:snowflake", "ClimateMaxACOn", _climate("set_max_ac", "ON")),
    114: RemoteCommand(114, "tat_max_ac", "Tắt Max AC", "mdi:snowflake-off", "ClimateMaxACOff", _climate("set_max_ac", "OFF")),
    115: RemoteCommand(115, "bat_ionizer", "Bật ionizer", "mdi:air-purifier", "ClimateIonizerOn", _climate("set_ionlizer", "ON")),
    116: RemoteCommand(116, "tat_ionizer", "Tắt ionizer", "mdi:air-purifier", "ClimateIonizerOff", _climate("set_ionlizer", "OFF")),
    117: RemoteCommand(117, "lay_gio_trong", "Lấy gió trong", "mdi:air-recirculate", "ClimateAirCirculationInternal", _climate_recirculation("INTER")),
    118: RemoteCommand(118, "lay_gio_ngoai", "Lấy gió ngoài", "mdi:weather-windy", "ClimateAirCirculationOuter", _climate_recirculation("OUTER")),
    119: RemoteCommand(119, "bat_so_kinh_truoc", "Bật sấy kính trước", "mdi:car-defrost-front", "ClimateFrontDefrostOn", _climate("set_front_defrost_mode", "ON")),
    120: RemoteCommand(120, "tat_so_kinh_truoc", "Tắt sấy kính trước", "mdi:car-defrost-front", "ClimateFrontDefrostOff", _climate("set_front_defrost_mode", "OFF")),
    121: RemoteCommand(121, "dat_nhiet_do_ghe_phu", "Đặt nhiệt độ ghế phụ", "mdi:thermometer", "ClimatePassengersTemp", _climate_passenger_temp),
    122: RemoteCommand(122, "lich_dieu_hoa_bat", "Lịch điều hoà: bật", "mdi:calendar-clock", "ClimateScheduleOn", _climate_schedule("TURN_ON_SCHEDULE")),
    123: RemoteCommand(123, "lich_dieu_hoa_tat", "Lịch điều hoà: tắt", "mdi:calendar-clock", "ClimateScheduleOff", _climate_schedule("TURN_OFF_SCHEDULE")),
    124: RemoteCommand(124, "fota_tai_bat_dau", "FOTA: bắt đầu tải", "mdi:download", "FotaControlDownloadStart", _fota_download("START_DOWNLOAD")),
    125: RemoteCommand(125, "fota_tai_tam_dung", "FOTA: tạm dừng tải", "mdi:pause", "FotaControlDownloadPause", _fota_download("PAUSE_DOWNLOAD")),
    126: RemoteCommand(126, "fota_tai_tiep", "FOTA: tải tiếp", "mdi:play", "FotaControlDownloadResume", _fota_download("RESUME_DOWNLOAD")),
    127: RemoteCommand(127, "fota_tai_huy", "FOTA: huỷ tải", "mdi:close-octagon", "FotaControlDownloadStop", _fota_download("CANCEL_DOWNLOAD")),
    128: RemoteCommand(128, "fota_cai_ngay", "FOTA: cài ngay", "mdi:package-up", "FotaControlInstallNow", _fota_install_now),
    129: RemoteCommand(129, "fota_tu_dong_bat", "FOTA: bật tự động tải", "mdi:cloud-download", "FotaConfigScheduleEnable", _fota_auto_download(True)),
    130: RemoteCommand(130, "fota_tu_dong_tat", "FOTA: tắt tự động tải", "mdi:cloud-off-outline", "FotaConfigScheduleDisable", _fota_auto_download(False)),
    131: RemoteCommand(131, "fota_cau_hinh_mang", "FOTA: cho phép tải qua LTE", "mdi:signal-cellular-2", "FotaConfigSetDownloadConfig", _fota_download_config),
    132: RemoteCommand(132, "fota_dat_lich", "FOTA: đặt lịch", "mdi:calendar-arrow-right", "FotaConfigSetSchedule", _fota_schedule),
}

#: Toàn bộ lệnh (mặc định + mở rộng) dùng cho tra cứu theo id/slug/use case.
ALL_COMMANDS: dict[int, RemoteCommand] = {**COMMANDS, **EXTRA_COMMANDS}
COMMAND_BY_SLUG_ALL: dict[str, RemoteCommand] = {c.slug: c for c in ALL_COMMANDS.values()}
COMMAND_BY_USE_CASE_ALL: dict[str, RemoteCommand] = {c.use_case: c for c in ALL_COMMANDS.values()}

#: Lệnh test của app: ``message_name`` và ``tag`` khác các lệnh thường.
TEST_COMMAND = RemoteCommand(
    99,
    "test_command",
    "Lệnh kiểm thử",
    "mdi:flask-outline",
    "Test",
    lambda params: _compact({"name": params.get("name", "TEST")}),
    message_name=MESSAGE_NAME_TEST_COMMAND,
    tag="TEST",
)


def resolve_command(command: Any) -> RemoteCommand:
    """Chấp nhận mã số (1..22 hoặc 101..132), slug (``khoa_cua``) hoặc use case (``DoorsLock``)."""
    if isinstance(command, RemoteCommand):
        return command
    if isinstance(command, bool):
        raise RemoteControlError(f"Mã lệnh không hợp lệ: {command!r}")
    if isinstance(command, int):
        cmd = ALL_COMMANDS.get(command)
        if cmd is None:
            raise RemoteControlError(
                f"Mã lệnh {command} không tồn tại. Dải cơ bản: {min(COMMANDS)}–{max(COMMANDS)}, "
                f"mở rộng: {min(EXTRA_COMMANDS)}–{max(EXTRA_COMMANDS)}."
            )
        return cmd
    key = str(command or "").strip()
    if key in COMMAND_BY_USE_CASE_ALL:
        return COMMAND_BY_USE_CASE_ALL[key]
    if key in COMMAND_BY_SLUG_ALL:
        return COMMAND_BY_SLUG_ALL[key]
    if key.lower() in COMMAND_BY_SLUG_ALL:
        return COMMAND_BY_SLUG_ALL[key.lower()]
    if key == "Test":
        return TEST_COMMAND
    raise RemoteControlError(f"Không nhận diện được lệnh: {command!r}")


# ---------------------------------------------------------------------------
# Dựng body v2
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ControlCredentials:
    """Thông tin pairing cần để ký lệnh."""

    user_id: str
    session_id: str
    private_key_pem: str
    share_key: str | None = None
    is_master_profile: bool = True
    wakeup_timeout_ms: int = DEFAULT_WAKEUP_TIMEOUT_MS


def missing_credentials(creds: ControlCredentials) -> list[str]:
    """Trả về danh sách trường pairing còn thiếu (rỗng nghĩa là đủ).

    ``session_id`` **không** bắt buộc: ``sess_id`` là mã tương quan phía client.
    Bằng chứng: probe thật 2026-09-17 với ``sess_id`` là UUID ngẫu nhiên — server
    không phàn nàn gì về giá trị này (xem DIEU_KHIEN_REMOTE_CONTROL.md muc 12).
    """
    missing = []
    if not (creds.user_id or "").strip():
        missing.append("user_id")
    if not (creds.private_key_pem or "").strip():
        missing.append("private_key_pem")
    return missing


def build_remote_command_payload(
    command: RemoteCommand,
    credentials: ControlCredentials,
    params: Mapping[str, Any] | None = None,
    *,
    timestamp_ms: int | None = None,
) -> dict[str, Any]:
    """Dựng body ``RemoteDataRequest`` đúng như ``RemoteControlManager.O0``.

    Raises:
        RemoteControlError: thiếu credential, PEM hỏng, hoặc ``message_content``
            không dựng được. Không bao giờ trả về body thiếu chữ ký.
    """
    params = dict(params or {})
    missing = missing_credentials(credentials)
    if missing:
        raise RemoteControlError(
            "Thiếu thông tin pairing để ký lệnh điều khiển: " + ", ".join(missing)
        )

    if timestamp_ms is None:
        import time

        timestamp_ms = int(time.time() * 1000)

    session_id = (credentials.session_id or "").strip()
    if not session_id:
        # sess_id là mã tương quan phía client; app lấy PairData.g() (ssid) nhưng
        # PairData không được lưu xuống DB nên giá trị này không bền.
        import uuid

        session_id = f"ha-{uuid.uuid4()}"
        _LOGGER.debug("VinFast: sess_id không cấu hình, dùng mã tương quan %s", session_id)

    content_json = command.build_content(params)
    # Bước 1: base64 nội dung lệnh — đây là thứ được ký và cũng là thứ gửi lên.
    encoded_content = encode_base64_no_wrap(content_json.encode("utf-8"))
    timestamp = str(timestamp_ms)

    chunks = [timestamp.encode("utf-8"), encoded_content.encode("utf-8")]

    private_key = load_private_key(credentials.private_key_pem)
    signature = rsa_sign_base64(private_key, chunks)

    signature2: str | None = None
    if credentials.share_key and credentials.share_key.strip():
        try:
            share_key_bytes = decode_base64_no_wrap(credentials.share_key.strip())
        except Exception as exc:  # noqa: BLE001
            raise RemoteControlError(f"Share key không phải Base64 NO_WRAP hợp lệ: {exc}") from exc
        signature2 = encode_base64_no_wrap(hmac_sha256(share_key_bytes, chunks))

    payload: dict[str, Any] = {
        "message_name": command.message_name,
        "message_content": encoded_content,
        "sess_id": session_id,
        "timestamp": timestamp,
        "signature": signature,
        "tag": command.tag,
        "user_id": user_id_hash(credentials.user_id.strip()),
        "isMasterProfile": bool(credentials.is_master_profile),
        "signature2": signature2,
        "wakeUpTimeOut": timestamp_ms + int(credentials.wakeup_timeout_ms),
    }
    return payload


def parse_command_response(body: Any) -> tuple[bool, int | None, str | None]:
    """Đọc phản hồi API điều khiển → ``(ok, control_error_code, message)``.

    ``BaseResponse`` của app dùng ``code = 200000`` cho thành công (không phải 200);
    quan sát thực tế ngày 2026-09-17: thành công ``200000``, lỗi ``262144``/``262150``.
    ``RemoteDataDto`` chỉ có ``{isConnected, lastUpdateTime, currentAction}``.
    """
    if not isinstance(body, dict):
        return False, None, None
    code = body.get("code")
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    try:
        numeric = int(code) if code is not None else None
    except (TypeError, ValueError):
        numeric = None
    if numeric is not None:
        ok = numeric in (200000, 0, 200, 201, 202, 204)
    else:
        ok = bool(data)
    error_code = data.get("control_errorcode")
    message = body.get("message") or data.get("message") or data.get("currentAction")
    if body.get("error") and body.get("error") != message:
        message = f"{body.get('error')}" + (f" — {message}" if message else "")
    if error_code is not None and message:
        message = f"{message} (control_errorcode={error_code})"
    return bool(ok), error_code, message
