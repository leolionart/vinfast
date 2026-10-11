import logging
from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    async_add_entities([VinFastDeviceTracker(api)])

class VinFastDeviceTracker(TrackerEntity):
    def __init__(self, api):
        self.api = api
        self._attr_has_entity_name = True
        self._attr_name = "Vị trí GPS"
        
        # =================================================================
        model_slug = slugify(getattr(api, "vehicle_model_display", "VF")).replace("_", "")
        vin_slug = api.vin.lower() if api.vin else "unknown"
        
        # Ép Unique ID mới
        self._attr_unique_id = f"{model_slug}_{vin_slug}_tracker"
        # Ép Entity ID chuẩn
        self.entity_id = f"device_tracker.{model_slug}_{vin_slug}_vi_tri_gps"
        # =================================================================

        veh_name = getattr(api, 'vehicle_name', '')
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, api.vin)},
            name=f"{getattr(api, 'vehicle_model_display', 'VinFast')} {veh_name}".strip(),
            manufacturer="VinFast",
            model=getattr(api, "vehicle_model_display", "EV"),
        )

    @property
    def latitude(self):
        # [2.9.56] Bỏ fallback ``34185_00001_00001``: theo từ điển alias của server đó là
        # VEHICLE_CRASH_STATUS_SIDE_LEFT_CRASH (0/1), không phải vĩ độ.
        lat = self.api._last_data.get("api_last_lat", self.api._last_data.get("00006_00001_00000"))
        return self._coordinate(lat, -90.0, 90.0)

    @property
    def longitude(self):
        lon = self.api._last_data.get("api_last_lon", self.api._last_data.get("00006_00001_00001"))
        return self._coordinate(lon, -180.0, 180.0)

    @staticmethod
    def _coordinate(value, minimum, maximum):
        try:
            coordinate = float(value)
        except (TypeError, ValueError):
            return None
        return coordinate if minimum <= coordinate <= maximum else None

    @property
    def source_type(self):
        return "gps"

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        def handle_new_data(data):
            try:
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
            except Exception:
                _LOGGER.debug("VinFast: bỏ qua tracker update sau unload", exc_info=True)
        self._remove_callback = self.api.add_callback(handle_new_data)

    async def async_will_remove_from_hass(self):
        remove_callback = getattr(self, "_remove_callback", None)
        if remove_callback:
            remove_callback()
            self._remove_callback = None
        await super().async_will_remove_from_hass()
