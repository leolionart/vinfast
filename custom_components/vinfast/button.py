import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.util import slugify
import asyncio
import inspect

from .const import DOMAIN
from .remote_control import COMMANDS, EXTRA_COMMANDS

_LOGGER = logging.getLogger(__name__)


def _as_bool(value) -> bool:
    """Chấp nhận bool thật, chuỗi 'true/1/on/yes' (dữ liệu trong .storage là JSON)."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")

# ---------------------------------------------------------------------------
# [LEGACY v2.9.45 - giữ lại để tham chiếu/rollback, KHÔNG dùng]
#
# Bảng lệnh cũ dựa trên giả định API điều khiển nhận `commandType` dạng số 1..20.
# Giả định này SAI: `base_1.apk` không có `commandType`; endpoint thật là
# POST /ccaraccessmgmt/api/v2/remote/app/command với body RemoteDataRequest và
# bắt buộc có `signature`. Xem DIEU_KHIEN_REMOTE_CONTROL.md muc 8.
# Danh mục lệnh thật nằm ở `remote_control.COMMANDS`.
#
# KNOWN_COMMANDS = {
#     1: ("Khóa cửa", "mdi:lock", "khoa_cua"),
#     2: ("Mở cửa", "mdi:lock-open", "mo_cua"),
#     3: ("Bấm còi", "mdi:bullhorn", "bam_coi"),
#     4: ("Nháy đèn", "mdi:car-light-high", "nhay_den"),
#     5: ("Bật điều hòa", "mdi:fan", "bat_dieu_hoa"),
#     6: ("Tắt điều hòa", "mdi:fan-off", "tat_dieu_hoa"),
#     7: ("Mở cốp", "mdi:car-back", "mo_cop"),
# }
#
#     for cmd_id in range(1, 21):
#         if cmd_id in KNOWN_COMMANDS:
#             name, icon, slug = KNOWN_COMMANDS[cmd_id]
#         else:
#             name = f"Lệnh Raw (Mã {cmd_id})"
#             icon = "mdi:flask-outline"
#             slug = f"raw_cmd_{cmd_id}"
#         buttons.append(VinFastRemoteCommand(api, cmd_id, name, icon, slug))
# ---------------------------------------------------------------------------


async def async_setup_entry(hass, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    buttons = []

    # 1. TẠO NÚT LOCAL: TÌM TRẠM SẠC
    buttons.append(VinFastLocalAction(api, "Tìm trạm sạc", "mdi:ev-station", "tim_tram_sac", "fetch_nearby_stations"))

    # 2. TẠO NÚT NẮN BẢN ĐỒ (MAGIC STAFF)
    buttons.append(VinFastFixMapButton(api))

    # 2b. NÚT LÀM MỚI DỮ LIỆU MỞ RỘNG (chẩn đoán, bảo hành, Battery Care, FOTA...)
    buttons.append(VinFastRefreshExtendedButton(api))

    # 3. TẠO CÁC NÚT REMOTE COMMAND theo danh mục lệnh thật của APK.
    #    Dải id 1..7 giữ nguyên slug cũ để không phá entity id mà thẻ Lovelace
    #    đang gọi trực tiếp (khoa_cua, mo_cua, bam_coi, nhay_den, ...).
    for cmd_id in sorted(COMMANDS):
        spec = COMMANDS[cmd_id]
        buttons.append(VinFastRemoteCommand(api, cmd_id, spec.name, spec.icon, spec.slug))

    # 3b. LỆNH MỞ RỘNG (32 lệnh khai thác thêm từ APK 2.25.7: capo, cửa sổ trời,
    #     SOC mục tiêu, lịch sạc/điều hoà, FOTA, các nhánh điều hoà...).
    #     Mặc định TẮT để không đẻ thêm ~32 nút; bật bằng tuỳ chọn
    #     `control_advanced_buttons`. Vẫn gọi được qua service với slug/use case.
    options = {**(config_entry.data or {}), **(config_entry.options or {})}
    if _as_bool(options.get("control_advanced_buttons", False)):
        for cmd_id in sorted(EXTRA_COMMANDS):
            spec = EXTRA_COMMANDS[cmd_id]
            buttons.append(VinFastRemoteCommand(api, cmd_id, spec.name, spec.icon, spec.slug))

    async_add_entities(buttons)


class VinFastLocalAction(ButtonEntity):
    def __init__(self, api, name, icon, slug, action_method):
        self.api = api
        self._action_method = action_method
        self._attr_has_entity_name = True
        self._attr_name = name
        self._attr_icon = icon
        
        model_slug = slugify(getattr(api, "vehicle_model_display", "VF")).replace("_", "")
        vin_slug = api.vin.lower() if api.vin else "unknown"
        
        self._attr_unique_id = f"{model_slug}_{vin_slug}_{slug}"
        self.entity_id = f"button.{model_slug}_{vin_slug}_{slug}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.api.vin)},
            "name": f"{getattr(self.api, 'vehicle_model_display', 'VinFast')} {getattr(self.api, 'vehicle_name', '')}".strip(),
            "manufacturer": "VinFast",
            "model": getattr(self.api, "vehicle_model_display", "EV")
        }

    async def async_press(self) -> None:
        if hasattr(self.api, self._action_method):
            method = getattr(self.api, self._action_method)
            if inspect.iscoroutinefunction(method):
                await method()
            else:
                result = await self.hass.async_add_executor_job(method)
                if inspect.isawaitable(result):
                    await result
            _LOGGER.info(f"VinFast: Đã chạy hàm nội bộ [{self._attr_name}]")


class VinFastFixMapButton(ButtonEntity):
    def __init__(self, api):
        self.api = api
        self._attr_has_entity_name = True
        self._attr_name = "Tối ưu Bản đồ"
        self._attr_icon = "mdi:magic-staff"
        
        model_slug = slugify(getattr(api, "vehicle_model_display", "VF")).replace("_", "")
        vin_slug = api.vin.lower() if api.vin else "unknown"
        
        self._attr_unique_id = f"{model_slug}_{vin_slug}_fix_map"
        self.entity_id = f"button.{model_slug}_{vin_slug}_fix_map"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.api.vin)},
            "name": f"{getattr(self.api, 'vehicle_model_display', 'VinFast')} {getattr(self.api, 'vehicle_name', '')}".strip(),
            "manufacturer": "VinFast",
            "model": getattr(self.api, "vehicle_model_display", "EV")
        }

    async def async_press(self) -> None:
        # [2.9.54] WARNING -> INFO: hành động người dùng, không phải cảnh báo.
        _LOGGER.info("VinFast: Đã bấm nút Tối ưu Bản đồ. Đang ép chạy lại thuật toán (Force=True)...")
        if hasattr(self.api, "async_fix_all_historical_trips"):
            self.hass.async_create_task(self.api.async_fix_all_historical_trips(force=True))
        else:
            _LOGGER.error("VinFast: Lỗi - Không tìm thấy hàm nắn đường trong api.py")


class VinFastRefreshExtendedButton(ButtonEntity):
    """Làm mới dữ liệu mở rộng: chẩn đoán, bảo hành, Battery Care, FOTA, thuê pin..."""

    def __init__(self, api):
        self.api = api
        self._attr_has_entity_name = True
        self._attr_name = "Làm mới dữ liệu mở rộng"
        self._attr_icon = "mdi:cloud-refresh"

        model_slug = slugify(getattr(api, "vehicle_model_display", "VF")).replace("_", "")
        vin_slug = api.vin.lower() if api.vin else "unknown"

        self._attr_unique_id = f"{model_slug}_{vin_slug}_lam_moi_mo_rong"
        self.entity_id = f"button.{model_slug}_{vin_slug}_lam_moi_mo_rong"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.api.vin)},
            "name": f"{getattr(self.api, 'vehicle_model_display', 'VinFast')} {getattr(self.api, 'vehicle_name', '')}".strip(),
            "manufacturer": "VinFast",
            "model": getattr(self.api, "vehicle_model_display", "EV"),
        }

    async def async_press(self) -> None:
        if not hasattr(self.api, "refresh_extended"):
            _LOGGER.error("VinFast: api.py không có refresh_extended()")
            return
        count = await self.api.refresh_extended()
        # [2.9.54] WARNING -> INFO: hành động người dùng thành công.
        _LOGGER.info("VinFast: Đã làm mới dữ liệu mở rộng (%s khoá).", count)


class VinFastRemoteCommand(ButtonEntity):
    def __init__(self, api, cmd_id, name, icon, slug):
        self.api = api
        self._cmd_id = cmd_id
        self._attr_has_entity_name = True
        self._attr_name = name
        self._attr_icon = icon
        
        model_slug = slugify(getattr(api, "vehicle_model_display", "VF")).replace("_", "")
        vin_slug = api.vin.lower() if api.vin else "unknown"
        
        self._attr_unique_id = f"{model_slug}_{vin_slug}_{slug}"
        self.entity_id = f"button.{model_slug}_{vin_slug}_{slug}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.api.vin)},
            "name": f"{getattr(self.api, 'vehicle_model_display', 'VinFast')} {getattr(self.api, 'vehicle_name', '')}".strip(),
            "manufacturer": "VinFast",
            "model": getattr(self.api, "vehicle_model_display", "EV")
        }

    async def async_press(self) -> None:
        spec = COMMANDS.get(self._cmd_id)
        use_case = spec.use_case if spec else "?"
        # [2.9.54] WARNING -> INFO: gửi lệnh là hành động bình thường.
        _LOGGER.info(
            "VinFast: Đang gửi lệnh [%s] mã=%s use_case=%s", self._attr_name, self._cmd_id, use_case
        )
        result = await self.api.send_remote_command(self._cmd_id)
        if result:
            _LOGGER.info("VinFast: Lệnh %s (%s) thành công.", self._attr_name, use_case)
        else:
            _LOGGER.error("VinFast: Lệnh %s (%s) thất bại.", self._attr_name, use_case)