import logging
import json
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify

from .const import DOMAIN
from .const_common import SENSOR_SLUG_OVERRIDES, VIRTUAL_SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    sensors = []
    
    active_dict = VIRTUAL_SENSORS.copy()
    if hasattr(api, '_active_sensors'):
        active_dict.update(api._active_sensors)

    for device_key, (name, unit, icon, device_class) in active_dict.items():
        sensors.append(VinFastSensor(api, device_key, name, unit, icon, device_class))
        
    async_add_entities(sensors)

class VinFastSensor(SensorEntity):
    def __init__(self, api, device_key, name, unit, icon, device_class):
        self.api = api
        self._device_key = device_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class

        model_slug = slugify(getattr(api, "vehicle_model_display", "VF")).replace("_", "")
        vin_slug = api.vin.lower() if api.vin else "unknown"
        
        self._attr_unique_id = f"{model_slug}_{vin_slug}_{device_key}"
        # Một số tên có "Đ/đ" bị slugify() của HA xoá hẳn -> dùng slug ghi đè.
        entity_slug = SENSOR_SLUG_OVERRIDES.get(device_key) or slugify(name)
        self.entity_id = f"sensor.{model_slug}_{vin_slug}_{entity_slug}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.api.vin)},
            name=f"{getattr(self.api, 'vehicle_model_display', 'VinFast')} {getattr(self.api, 'vehicle_name', '')}".strip(),
            manufacturer="VinFast",
            model=getattr(self.api, "vehicle_model_display", "EV"),
            sw_version=self.api._last_data.get("00005_00001_00030", "Unknown")
        )

    async def async_added_to_hass(self):
        def handle_update(data):
            try:
                self.hass.loop.call_soon_threadsafe(self._process_update, data)
            except Exception:
                _LOGGER.debug("VinFast: bỏ qua update sau khi entity unload", exc_info=True)

        self._remove_callback = self.api.add_callback(handle_update)
        handle_update(self.api._last_data)

    async def async_will_remove_from_hass(self):
        remove_callback = getattr(self, "_remove_callback", None)
        if remove_callback:
            remove_callback()
            self._remove_callback = None
        await super().async_will_remove_from_hass()

    @callback
    def _process_update(self, data):
        if self._device_key in data:
            val = data[self._device_key]
            # None/rỗng = endpoint không còn trả dữ liệu -> trả entity về "unknown"
            # thay vì hiển thị chuỗi "NONE".
            if val is None or (isinstance(val, str) and val.strip() == ""):
                self._attr_native_value = None
                self._attr_extra_state_attributes = {}
                self.async_write_ha_state()
                return
            try:
                val_clean = str(int(float(val))) if isinstance(val, (int, float)) else str(val).strip().upper()
            except (TypeError, ValueError, OverflowError):
                val_clean = str(val).strip().upper()
            vi = getattr(self.api, "lang", "vi") == "vi"

            if self._device_key in ["34183_00001_00001", "34187_00000_00000"]:
                # ponytail: support aliases and letter codes for PRND position
                if val_clean in ["1", "P", "PARK"]: self._attr_native_value = "P (Đỗ)" if vi else "P (Park)"
                elif val_clean in ["2", "R", "REVERSE"]: self._attr_native_value = "R (Lùi)" if vi else "R (Reverse)"
                elif val_clean in ["3", "N", "NEUTRAL"]: self._attr_native_value = "N (Mo)" if vi else "N (Neutral)"
                elif val_clean in ["4", "D", "DRIVE"]: self._attr_native_value = "D (Đi)" if vi else "D (Drive)"
                else: self._attr_native_value = val

            elif self._device_key == "api_vehicle_image":
                val_str = str(val) if val else ""
                if val_str and "connected-car.vinfast.vn" in val_str:
                    self._attr_native_value = val_str.replace("https://", "http://")
                else:
                    self._attr_native_value = val_str

            elif self._device_key == "34183_00001_00029":
                if val_clean == "0": self._attr_native_value = "Nhả phanh tay" if vi else "Released"
                elif val_clean == "1": self._attr_native_value = "Kéo phanh tay" if vi else "Engaged"
                else: self._attr_native_value = val
                
            elif self._device_key == "34183_00001_00010":
                if val_clean == "2": self._attr_native_value = "Chưa sẵn sàng" if vi else "Not Ready"
                elif val_clean == "3": self._attr_native_value = "Sẵn sàng chạy (Ready)" if vi else "Ready to Drive"
                else: self._attr_native_value = val

            elif self._device_key == "34193_00001_00031":
                if val_clean == "1": self._attr_native_value = "Đã cắm súng sạc" if vi else "Plugged In"
                elif val_clean == "0": self._attr_native_value = "Chưa cắm súng sạc" if vi else "Unplugged"
                else: self._attr_native_value = val

            elif self._device_key in ["34193_00001_00005", "34183_00000_00001"]:
                if val_clean == "1": self._attr_native_value = "Đang sạc" if vi else "Charging"
                elif val_clean == "2": self._attr_native_value = "Sạc xong (Đầy)" if vi else "Fully Charged"
                elif val_clean in ["0", "3", "4"]: self._attr_native_value = "Không Sạc" if vi else "Not Charging"
                else: self._attr_native_value = val

            elif self._device_key == "34213_00001_00003":
                if val_clean == "1": self._attr_native_value = "Đã Khóa" if vi else "Locked"
                elif val_clean == "0": self._attr_native_value = "Mở Khóa" if vi else "Unlocked"
                else: self._attr_native_value = val

            elif self._device_key == "34234_00001_00003":
                if val_clean in ["1", "2"]: self._attr_native_value = "Đã Bật An Ninh" if vi else "Armed"
                elif val_clean == "0": self._attr_native_value = "Đã Tắt An Ninh" if vi else "Disarmed"
                else: self._attr_native_value = val

            # --- LOGIC PHÂN BIỆT THÔNG MINH CHO MÃ 34206 ---
            elif self._device_key == "34206_00001_00001":
                if self._attr_name == "Khóa tổng": # Xử lý cho nhóm VF5/6/7
                    if val_clean == "1": self._attr_native_value = "Đã Khóa" if vi else "Locked"
                    elif val_clean == "0": self._attr_native_value = "Mở Khóa" if vi else "Unlocked"
                    else: self._attr_native_value = val
                else: # Xử lý cho nhóm VF3/8/9 (Cắm trại)
                    if val_clean == "1": self._attr_native_value = "Đang Bật" if vi else "On"
                    elif val_clean == "0": self._attr_native_value = "Đã Tắt" if vi else "Off"
                    else: self._attr_native_value = val

            elif self._device_key in ["34205_00001_00001", "34207_00001_00001", "34186_00005_00004"]:
                if val_clean == "1": self._attr_native_value = "Đang Bật" if vi else "On"
                elif val_clean == "0": self._attr_native_value = "Đã Tắt" if vi else "Off"
                else: self._attr_native_value = val

            elif self._device_key.startswith("10351_"):
                if val_clean == "0": self._attr_native_value = "Đóng kín" if vi else "Closed"
                elif val_clean == "1": self._attr_native_value = "Đang mở" if vi else "Open"
                else: self._attr_native_value = val

            elif self._device_key.startswith("34215_"):
                if val_clean == "1": self._attr_native_value = "Đóng kín" if vi else "Closed"
                elif val_clean == "2": self._attr_native_value = "Đang mở" if vi else "Open"
                elif val_clean == "0": self._attr_native_value = "Đóng kín" if vi else "Closed"
                else: self._attr_native_value = val

            elif self._device_key == "34184_00001_00004":
                if val_clean == "0": self._attr_native_value = "Tắt" if vi else "Off"
                elif val_clean == "1": self._attr_native_value = "Bật" if vi else "On"
                else: self._attr_native_value = val

            elif self._device_key == "34184_00001_00011":
                if val_clean == "0": self._attr_native_value = "Lấy gió ngoài" if vi else "Fresh Air"
                elif val_clean == "1": self._attr_native_value = "Lấy gió trong" if vi else "Recirculation"
                else: self._attr_native_value = val

            elif self._device_key == "34184_00001_00012":
                if val_clean == "1": self._attr_native_value = "Gió mặt" if vi else "Face"
                elif val_clean == "2": self._attr_native_value = "Gió mặt & chân" if vi else "Face & Floor"
                elif val_clean == "3": self._attr_native_value = "Gió chân" if vi else "Floor"
                elif val_clean == "4": self._attr_native_value = "Gió kính & chân" if vi else "Defrost & Floor"
                elif val_clean == "0": self._attr_native_value = "Gió mặt (Auto)" if vi else "Face (Auto)"
                else: self._attr_native_value = val

            elif self._device_key == "34184_00001_00009":
                if val_clean == "0": self._attr_native_value = "Tắt sấy" if vi else "Defrost Off"
                elif val_clean == "1": self._attr_native_value = "Bật sấy kính lái" if vi else "Defrost On"
                else: self._attr_native_value = val

            elif self._device_key in ["34213_00004_00003", "56789_00001_00005"]:
                if val_clean == "0": self._attr_native_value = "Tắt" if vi else "Off"
                elif val_clean == "1": self._attr_native_value = "Bật" if vi else "On"
                else: self._attr_native_value = val

            elif self._device_key in ["34184_00001_00025", "34184_00001_00041"]:
                self._attr_native_value = val_clean

            elif self._device_key in ["00006_00001_00000", "00006_00001_00001"]:
                try:
                    filtered_key = "api_last_lat" if self._device_key.endswith("00000") else "api_last_lon"
                    num_val = float(self.api._last_data.get(filtered_key, val))
                    if num_val == 0.0: self._attr_native_value = "Đang tìm GPS..." if vi else "Searching GPS..."
                    else: self._attr_native_value = round(num_val, 6)
                except (ValueError, TypeError):
                    self._attr_native_value = "Không có tín hiệu" if vi else "No Signal"

            elif self._device_key == "api_trip_route":
                self._attr_native_value = "Dữ liệu Map" if vi else "Map Data"
                self._attr_extra_state_attributes = {"route_json": val if isinstance(val, str) else json.dumps(val)}
                
            elif self._device_key == "api_driving_trend_json":
                self._attr_native_value = "Dữ liệu Xu hướng" if vi else "Trend Data"
                self._attr_extra_state_attributes = {"trend_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key == "api_est_charge_completion_time":
                if val:
                    parsed = datetime.fromisoformat(str(val))
                    self._attr_native_value = parsed if parsed.tzinfo else parsed.astimezone()
                else:
                    self._attr_native_value = None
                
            elif self._device_key == "api_nearby_stations":
                self._attr_native_value = "Danh sách Trạm" if vi else "Station List"
                self._attr_extra_state_attributes = {"stations": val if isinstance(val, str) else json.dumps(val)}

            # --- API mở rộng: khoá chứa JSON dài -> state ngắn + attribute ---
            elif self._device_key == "api_alert_json":
                self._attr_native_value = "Chi tiết cảnh báo" if vi else "Alert Detail"
                self._attr_extra_state_attributes = {"alerts_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key == "api_driving_score_json":
                self._attr_native_value = "Chi tiết điểm lái" if vi else "Score Detail"
                self._attr_extra_state_attributes = {"indicators_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key == "api_parked_images":
                self._attr_native_value = "Ảnh vị trí đỗ" if vi else "Parked Images"
                self._attr_extra_state_attributes = {"images_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key == "api_current_charging_session":
                self._attr_native_value = "Phiên sạc hiện tại" if vi else "Current Session"
                self._attr_extra_state_attributes = {"session_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key == "api_firmware_last_ok":
                self._attr_native_value = "Đã cập nhật firmware" if vi else "Firmware Updated"
                self._attr_extra_state_attributes = {"firmware_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key == "api_firmware_in_progress":
                self._attr_native_value = "Đang cập nhật firmware" if vi else "Firmware Updating"
                self._attr_extra_state_attributes = {"firmware_json": val if isinstance(val, str) else json.dumps(val)}

            elif self._device_key in ("api_last_charge_time", "api_thief_time",
                                      "api_next_maintenance_date"):
                # device_class "timestamp" yêu cầu datetime có tzinfo, không nhận epoch thô
                # và CŨNG KHÔNG nhận chuỗi ISO (đã gây ValueError làm hỏng job cập nhật).
                # `api_next_maintenance_date` do parser trả về chuỗi ISO; hai cái còn lại là epoch.
                try:
                    if isinstance(val, datetime):
                        self._attr_native_value = val
                    elif isinstance(val, str) and val.strip():
                        self._attr_native_value = datetime.fromisoformat(
                            val.strip().replace("Z", "+00:00")
                        )
                    else:
                        ts = float(val)
                        if ts <= 0:
                            self._attr_native_value = None
                        else:
                            seconds = ts / 1000.0 if ts > 1e11 else ts
                            self._attr_native_value = datetime.fromtimestamp(
                                seconds, tz=datetime.now().astimezone().tzinfo
                            )
                except (TypeError, ValueError):
                    self._attr_native_value = None

            elif self._device_key in ("api_alert_summary", "api_thief_message",
                                      "api_battery_charging_habits", "api_battery_driving_habits",
                                      "api_battery_parking_habits"):
                val_str = str(val) if val else ""
                self._attr_native_value = val_str[:250] + "..." if len(val_str) > 250 else val_str
                if len(val_str) > 250:
                    self._attr_extra_state_attributes = {"full_text": val_str}

            elif self._device_key == "api_public_charge_sessions":
                self._attr_native_value = val
                history_str = self.api._last_data.get("api_charge_history_list", "[]")
                try:
                    history_data = json.loads(history_str) if isinstance(history_str, str) else history_str
                    formatted_history = []
                    for item in history_data:
                        date = item.get("date", "")
                        address = item.get("address", "")[:35]
                        kwh = item.get("kwh", 0)
                        dur = item.get("duration", 0)
                        formatted_history.append(f"{date} | {kwh} kWh ({dur} {'phút' if vi else 'mins'}) | {address}")
                    self._attr_extra_state_attributes = {("Lịch sử chi tiết" if vi else "Detailed History"): formatted_history if formatted_history else (["Chưa có dữ liệu"] if vi else ["No data"])}
                except Exception:
                    self._attr_extra_state_attributes = {"Lỗi" if vi else "Error": "Không thể parse dữ liệu sạc" if vi else "Parse error"}

            elif self._device_key == "api_home_charge_sessions":
                self._attr_native_value = val
                try:
                    home_kwh = float(self.api._last_data.get("api_home_charge_kwh", 0.0))
                except (TypeError, ValueError):
                    home_kwh = 0.0
                self._attr_extra_state_attributes = {("Tổng điện năng (kWh)" if vi else "Total Energy (kWh)"): round(home_kwh, 2)}

            elif self._device_key == "api_best_efficiency_band":
                attrs = {}
                stats = getattr(self.api, '_eff_stats', {})
                for k, v in stats.items():
                    if not isinstance(v, dict):
                        continue
                    drops = float(v.get("drops", 0) or 0)
                    distance = float(v.get("dist", 0) or 0)
                    if drops > 0:
                        attrs[f"Dải {k} km/h" if vi else f"Band {k} km/h"] = f"{round(distance / drops, 2)} km/1%"
                self._attr_extra_state_attributes = attrs if attrs else {("Trạng thái" if vi else "Status"): ("Chưa đủ dữ liệu sụt pin" if vi else "Not enough data")}
                self._attr_native_value = val

            elif self._device_key == "api_ai_advisor":
                val_str = str(val) if val else ("Chờ AI phân tích..." if vi else "Waiting for AI...")
                self._attr_extra_state_attributes = {"full_text": val_str}
                self._attr_native_value = val_str[:250] + "..." if len(val_str) > 250 else val_str

            elif self._device_key == "api_total_charge_sessions":
                try:
                    pub = int(float(self.api._last_data.get("api_public_charge_sessions", 0)))
                    home = int(float(self.api._last_data.get("api_home_charge_sessions", 0)))
                    self._attr_native_value = pub + home
                    self._attr_extra_state_attributes = {
                        "Sạc tại trạm": pub,
                        "Sạc tại nhà": home
                    }
                except Exception:
                    self._attr_native_value = val

            elif self._device_key == "api_debug_raw":
                try:
                    raw_dict = getattr(self.api, '_raw_json_dict', {})
                    if raw_dict:
                        self._attr_extra_state_attributes = raw_dict.copy()
                    else:
                        self._attr_extra_state_attributes = {"Trạng thái": "Chờ bản tin MQTT..."}
                    val_str = str(val) if val else "Đang hoạt động"
                    self._attr_native_value = val_str[:250] + "..." if len(val_str) > 250 else val_str
                except Exception:
                    _LOGGER.debug("VinFast: không thể tạo debug attributes", exc_info=True)
                
            elif self._device_key in ["34183_00001_00003", "34199_00000_00000"]:
                try: odo_val = float(val)
                except: odo_val = 0.0
                if odo_val <= 0.0:
                    try:
                        fb = float(self.api._last_data.get("api_odo_fallback_estimate", 0))
                    except (TypeError, ValueError):
                        fb = 0.0
                    if fb > 0:
                        self._attr_native_value = fb
                        self._attr_extra_state_attributes = {"odo_source": self.api._last_data.get("api_odo_fallback_source", "Lịch sử lái xe"), "is_estimated": True}
                    else: self._attr_native_value = "Đang ước lượng..." if vi else "Estimating..."
                else:
                    self._attr_native_value = round(odo_val, 2)
                    self._attr_extra_state_attributes = {"odo_source": "AWS MQTT Thực tế", "is_estimated": False}
                    
            else:
                if isinstance(val, float):
                    self._attr_native_value = round(val, 2)
                else:
                    val_str = str(val)
                    self._attr_native_value = val_str[:250] + "..." if len(val_str) > 250 else val_str

            self.async_write_ha_state()
