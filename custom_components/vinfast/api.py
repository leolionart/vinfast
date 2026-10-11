import os
import json
import time
import logging
import threading
import asyncio
import datetime
import tempfile
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from .const import REGION_CONFIG
from .api_auth import AuthManager
from .api_mqtt import MQTTManager
from .api_helpers import calculate_speed_band_efficiency, safe_float
from .extended_api import ExtendedApiClient
from .trip_storage import TripStorageManager

_LOGGER = logging.getLogger(__name__)

class VinFastAPI:
    def __init__(self, email, password, vin=None, vehicle_name="Xe VinFast", region="VN", lang="vi", options=None, gemini_api_key=""):
        self.email = str(email or "").strip()
        self.password = str(password or "").strip()
        self.region = region
        self.lang = lang
        self.gemini_api_key = gemini_api_key.strip() if gemini_api_key else ""
        self.vin = vin
        self.user_id = None
        self.vehicle_name = vehicle_name
        self.vehicle_model_display = "Unknown" 
        self.options = options or {}
        
        cfg = REGION_CONFIG.get(self.region, REGION_CONFIG["VN"])
        self.auth0_domain = cfg["AUTH0_DOMAIN"]
        self.auth0_client_id = cfg["AUTH0_CLIENT_ID"]
        self.api_base = cfg["API_BASE"]
        self.aws_region = cfg["AWS_REGION"]
        self.cognito_pool_id = cfg["COGNITO_POOL_ID"]
        self.iot_endpoint = cfg["IOT_ENDPOINT"]
        
        # Biến Auth mới
        self.access_token = None
        self.vf_token = None
        self.private_key = None 
        
        self._running = False
        self.callbacks = []
        
        ai_state = ("Hệ thống AI đang chờ..." if self.lang == "vi" else "AI is waiting...") if self.gemini_api_key else "DISABLED"
        
        self._last_data = {
            "api_vehicle_status": "Đang kết nối..." if self.lang == "vi" else "Connecting...",
            "api_current_address": "Đang tải..." if self.lang == "vi" else "Loading...",
            "api_trip_route": "[]",
            "api_nearby_stations": "[]",
            "api_trip_distance": 0.0,
            "api_trip_avg_speed": 0.0,
            "api_trip_energy_used": 0.0,
            "api_trip_efficiency": 0.0,
            "api_live_charge_power": 0.0,
            "api_last_charge_start_soc": 0.0, 
            "api_last_charge_end_soc": 0.0,   
            "api_last_lat": None, 
            "api_last_lon": None,
            "api_total_charge_sessions": 0,
            "api_public_charge_sessions": 0, 
            "api_total_energy_charged": 0.0,
            "api_vehicle_name": self.vehicle_name,
            "api_charge_history_list": "[]", 
            "api_home_charge_kwh": 0.0,
            "api_home_charge_sessions": 0,
            "api_ai_advisor": ai_state,
            "api_security_warning": "An toàn" if self.lang == "vi" else "Safe",
            "api_calc_range_per_percent": 0.0,
            "api_est_range_degradation": 0.0,
            "api_debug_raw": "Chờ kết nối MQTT..." if self.lang == "vi" else "Waiting for MQTT...",
            "api_odo_fallback_estimate": 0.0,
            "api_odo_fallback_source": "Chưa xác định"
        }  
        
        self._is_moving = False
        self._is_charging = False
        self._last_is_charging = False 
        self._last_actual_move_time = time.time()
        self._is_parked = False
        self._parked_since = None
        self._last_lat_lon = ""
        self._vehicle_offline = False
        self._last_auto_wakeup_time = 0
        
        self._is_trip_active = False
        self._trip_start_odo = 0.0
        self._trip_start_time = time.time()
        self._trip_start_soc = 100.0
        self._trip_start_address = "Unknown"
        self._route_coords = []
        self._last_gps_time = time.time()
        self._trip_accumulated_distance_m = 0.0
        self._pending_daily_rollover_date = None
        self._daily_rollover_after_ts = 0
        
        self._eff_initial_soc = None
        self._eff_start_soc = None
        self._eff_gps_dist = 0.0
        self._eff_ignored_first = False
        
        self._last_ai_anomaly_time = 0
        self._last_ai_weather_time = 0
        
        self._charge_start_time = time.time()
        self._charge_start_soc = 0.0
        self._charge_calc_soc = 0.0
        self._charge_calc_time = time.time()
        self._current_charge_max_power = 0.0 

        self._last_geocoded_grid = None
        self._last_weather_fetch_time = 0 
        self._last_mqtt_msg_time = time.time() 
        self._geocode_lock = threading.Lock()
        self._file_lock = threading.Lock()
        self.trip_store = None  # Khởi tạo sau khi hass/storage_dir sẵn sàng
        self.dynamic_alias_map = {}
        
        self._raw_json_dict = {}
        self._changelog_buffer = []

        self.auth = AuthManager(self)
        self.mqtt = MQTTManager(self)

    def _format_pem_string(self, pem_str: str) -> str:
        if not pem_str: return ""
        pem_str = pem_str.replace("\\n", "\n").replace("\\r", "")
        if pem_str.count('\n') > 2: return pem_str
        import re
        begin_marker = "-----BEGIN PRIVATE KEY-----"
        end_marker = "-----END PRIVATE KEY-----"
        if begin_marker in pem_str and end_marker in pem_str:
            start_idx = pem_str.find(begin_marker) + len(begin_marker)
            end_idx = pem_str.find(end_marker)
            b64_content = pem_str[start_idx:end_idx]
            b64_clean = re.sub(r'\s+', '', b64_content)
            lines = [begin_marker]
            for i in range(0, len(b64_clean), 64):
                lines.append(b64_clean[i:i+64])
            lines.append(end_marker)
            return "\n".join(lines)
        return pem_str

    def _load_private_key(self):
        try:
            from .const import CONF_VINFAST_PRIVATE_KEY
        except ImportError:
            CONF_VINFAST_PRIVATE_KEY = "vinfast_private_key"
        import os
        opts = self.options if hasattr(self, "options") else {}
        pem_data = opts.get(CONF_VINFAST_PRIVATE_KEY)
        if not pem_data and hasattr(self, "data") and self.data:
            pem_data = self.data.get(CONF_VINFAST_PRIVATE_KEY)

        if not pem_data:
            # No key in config – fallback to legacy PEM file if still present.
            pem_path = os.path.join(os.path.dirname(__file__), "vinfast_private.pem")
            if os.path.isfile(pem_path):
                try:
                    with open(pem_path, "r", encoding="utf-8") as f:
                        pem_raw = f.read()
                        formatted_pem = self._format_pem_string(pem_raw)
                        self.private_key = load_pem_private_key(formatted_pem.encode("utf-8"), password=None)
                        _LOGGER.warning(
                            "VinFast: Đọc PEM từ file cũ. Vào Tùy chọn → nhập khóa → xoá vinfast_private.pem."
                        )
                        return
                except Exception as e:
                    _LOGGER.error("VinFast: Đọc PEM file fallback thất bại – %s", e)
            _LOGGER.error("VinFast: Không có Private Key (PEM) trong cấu hình và không tìm thấy file PEM.")
            return
        
        try:
            formatted_pem = self._format_pem_string(str(pem_data))
            self.private_key = load_pem_private_key(formatted_pem.encode("utf-8"), password=None)
        except Exception as e:
            _LOGGER.error(f"VinFast: Lỗi đọc Private Key từ cấu hình - {e}")

    def add_callback(self, cb):
        if cb not in self.callbacks:
            self.callbacks.append(cb)
            if self._last_data:
                cb(self._last_data)

        def remove_callback():
            try:
                self.callbacks.remove(cb)
            except ValueError:
                pass

        return remove_callback

    def trigger_callbacks(self):
        for cb in tuple(self.callbacks):
            try:
                cb(self._last_data)
            except Exception:
                _LOGGER.exception("VinFast: callback update failed")

    async def login(self): return await self.auth.login()
    async def get_vehicles(self): return await self.auth.get_vehicles()
    async def send_remote_command(self, cmd, params=None): return await self.auth.send_remote_command(cmd, params)
    async def fetch_nearby_stations(self, force=True): return await self.auth.fetch_nearby_stations(force=force)

    # ==========================================
    # QUẢN LÝ LUỒNG CHẠY NGẦM & VÒNG ĐỜI
    # ==========================================
    def start_mqtt(self): 
        self._running = True
        # Khởi tạo dual-track storage (hass sẵn sàng tại đây)
        if self.vin and not self.trip_store:
            self.trip_store = TripStorageManager(self.storage_dir, self.vin)
            _LOGGER.info("VinFast: TripStorageManager khởi tạo tại %s", self.trip_store.directory)
        self.mqtt.start()
        
        # Kích hoạt luồng tự động tải JSON Lịch sử ngầm (Chống treo giao diện)
        if not getattr(self, '_history_task', None) or self._history_task.done():
            self._history_task = self.hass.loop.create_task(self._periodic_history_update())

        # Luồng dữ liệu mở rộng (chẩn đoán, bảo hành, Battery Care, FOTA...)
        if not getattr(self, '_extended_task', None) or self._extended_task.done():
            self._extended_task = self.hass.loop.create_task(self._periodic_extended_update())

    def stop(self):
        self._running = False
        for attr in ("_history_task", "_extended_task"):
            task = getattr(self, attr, None)
            if task and not task.done():
                self.hass.loop.call_soon_threadsafe(task.cancel)
        self.mqtt.stop()

    # ==========================================
    # DỮ LIỆU MỞ RỘNG (extended_api)
    # ==========================================
    async def refresh_extended(self) -> int:
        """Lấy dữ liệu mở rộng một lần. Trả về số khoá state được cập nhật."""
        if not getattr(self, "extended", None):
            self.extended = ExtendedApiClient(self)
        try:
            updates = await self.extended.refresh()
        except Exception:
            _LOGGER.exception("VinFast: cập nhật dữ liệu mở rộng thất bại")
            return 0
        if updates:
            self._last_data.update(updates)
            self.trigger_callbacks()
        _LOGGER.debug("VinFast: extended refresh cập nhật %d khoá", len(updates))
        return len(updates)

    async def _periodic_extended_update(self):
        """Vòng lặp nền: làm mới dữ liệu mở rộng mỗi 15 phút."""
        await asyncio.sleep(40)  # nhường chỗ cho login + MQTT ổn định
        while self._running:
            try:
                if self.vin:
                    await self.refresh_extended()
            except Exception:
                _LOGGER.exception("VinFast: lỗi vòng lặp dữ liệu mở rộng")
            for _ in range(900):
                if not self._running:
                    break
                await asyncio.sleep(1)

    async def _periodic_history_update(self):
        """Luồng chạy ngầm: Tự động cập nhật Lịch sử Sạc, Xu hướng lái xe mỗi 30 phút"""
        await asyncio.sleep(15) # Chờ 15s cho hệ thống MQTT kết nối ổn định trước
        
        while self._running:
            try:
                if self.vin:
                    _LOGGER.info("VinFast: Bắt đầu tiến trình cập nhật Lịch sử Sạc và Xu hướng lái xe...")
                    
                    # 1. Cập nhật Lịch sử Sạc (incremental cache)
                    if hasattr(self, 'auth') and hasattr(self.auth, 'fetch_charging_history'):
                        await self.auth.fetch_charging_history()

                    # 2. Lấy dữ liệu Xu hướng lái xe từ API VinFast (7d, 30d, 365d)
                    if hasattr(self, 'auth') and hasattr(self.auth, 'fetch_all_driving_trends'):
                        await self.auth.fetch_all_driving_trends()
                    if hasattr(self, 'auth') and hasattr(self.auth, 'fetch_full_driving_distance'):
                        await self.auth.fetch_full_driving_distance()
                        
                    # 3. Tính toán Thống kê Toàn Cục (Global Speed Bands) từ lịch sử chuyến đi
                    try:
                        trip_file = os.path.join(self.storage_dir, f"vinfast_trips_{self.vin.lower()}.json")
                        if os.path.exists(trip_file):
                            def _read_trip_file():
                                with open(trip_file, 'r', encoding='utf-8') as f:
                                    return json.load(f)
                            trips = await self.hass.async_add_executor_job(_read_trip_file)
                            self._last_data["api_global_speed_efficiency"] = json.dumps(calculate_speed_band_efficiency(trips))
                    except Exception as g_e:
                        _LOGGER.error(f"VinFast: Lỗi tính toán Global Speed Efficiency: {g_e}")

                    # 4. Kích hoạt cập nhật giao diện
                    self.trigger_callbacks()
                    
            except Exception as e:
                _LOGGER.error(f"VinFast: Lỗi ngầm trong luồng cập nhật Lịch sử - {e}")
            
            # Ngủ đông 30 phút (1800 giây) trước khi cập nhật mẻ tiếp theo
            for _ in range(1800):
                if not self._running: break
                await asyncio.sleep(1)


    # ==========================================
    # CÁC HÀM XỬ LÝ KHÁC
    # ==========================================
    def _update_vehicle_name(self, candidate_name):
        if not candidate_name: return
        candidate = str(candidate_name).strip()
        if len(candidate) < 2 or candidate.isnumeric() or candidate.lower() in ["0", "1", "none", "null", "unknown", "vinfast"]: return
        if "profile_email" in candidate.lower(): return
        self._last_data["api_vehicle_name"] = candidate

    def inject_mock_data(self, payload_list):
        class MockMsg:
            def __init__(self, data): self.payload = json.dumps(data).encode('utf-8')
        self.mqtt._on_message(None, None, MockMsg(payload_list))

    def _calculate_advanced_stats(self):
        try:
            target_spec = getattr(self, '_vehicle_spec', {"capacity": 0, "range": 0})
            cap = target_spec.get("capacity", 0)
            ran = target_spec.get("range", 0)
            
            if cap > 0:
                self._last_data["api_static_capacity"] = cap
                self._last_data["api_static_range"] = ran

                # --- Tổng hợp Tổng điện năng đã sạc từ lịch sử ---
                # Ưu tiên lấy từ api_charge_history_list (public sessions từ API VinFast)
                current_total = safe_float(self._last_data.get("api_total_energy_charged", 0))
                history_str = self._last_data.get("api_charge_history_list", "[]")
                public_kwh = 0.0
                try:
                    history_list = json.loads(history_str) if isinstance(history_str, str) else history_str
                    if isinstance(history_list, list):
                        public_kwh = sum(safe_float(s.get("kwh", 0)) for s in history_list)
                except Exception:
                    pass
                home_kwh = safe_float(self._last_data.get("api_home_charge_kwh", 0))
                aggregated_kwh = public_kwh + home_kwh
                # Chỉ cập nhật nếu giá trị mới lớn hơn giá trị đang có (tránh reset)
                if aggregated_kwh > current_total:
                    self._last_data["api_total_energy_charged"] = round(aggregated_kwh, 2)

                total_kwh = safe_float(self._last_data.get("api_total_energy_charged", 0))
                odo = safe_float(self._last_data.get("34183_00001_00003", self._last_data.get("34199_00000_00000", 0)))
                calc_max = 0
                
                # Ưu tiên 1: Lấy từ driving trend API (dữ liệu thực từ VinFast server)
                trend_lifetime_eff = 0.0
                trend_json_str = self._last_data.get("api_driving_trend_json", "")
                if trend_json_str:
                    try:
                        trend_data = json.loads(trend_json_str)
                        for period in ["365", "30", "7"]:
                            if period in trend_data:
                                eff_val = trend_data[period].get("efficiency_kwh_100km")
                                if eff_val and 5.0 <= float(eff_val) <= 40.0:
                                    trend_lifetime_eff = float(eff_val)
                                    break
                    except Exception:
                        pass
                
                if trend_lifetime_eff > 0:
                    self._last_data["api_lifetime_efficiency"] = round(trend_lifetime_eff, 2)
                    calc_max = cap / (trend_lifetime_eff / 100) if cap > 0 else 0
                    if calc_max > 0:
                        self._last_data["api_calc_max_range"] = round(calc_max, 1)
                # Ưu tiên 2: Tính từ total_kwh / ODO (nếu không có driving trend)
                elif total_kwh > 0 and odo > 0:
                    lifetime_eff = (total_kwh / odo) * 100
                    # Chỉ lấy nếu trong dải hợp lý (loại bỏ 15.0 hardcode)
                    if 5.0 <= lifetime_eff <= 40.0:
                        self._last_data["api_lifetime_efficiency"] = round(lifetime_eff, 2)
                        calc_max = cap / (lifetime_eff / 100) if cap > 0 else 0
                        if calc_max > 0:
                            self._last_data["api_calc_max_range"] = round(calc_max, 1)
                # Ưu tiên 3: Nếu đang có giá trị tốt (không phải 0 hay 15.0 hardcode), giữ nguyên
                else:
                    existing_eff = safe_float(self._last_data.get("api_lifetime_efficiency", 0))
                    if existing_eff > 0 and existing_eff != 15.0:
                        calc_max = cap / (existing_eff / 100) if cap > 0 else 0
                        if calc_max > 0:
                            self._last_data["api_calc_max_range"] = round(calc_max, 1)


                if ran > 0 and calc_max > 0:
                    degradation_range = ((ran - calc_max) / ran) * 100.0
                    self._last_data["api_est_range_degradation"] = max(0.0, round(degradation_range, 2))
                
                charge_energy = safe_float(self._last_data.get("api_last_charge_energy", 0))
                start_soc = safe_float(self._last_data.get("api_last_charge_start_soc", 0))
                end_soc = safe_float(self._last_data.get("api_last_charge_end_soc", 0))
                delta_soc = end_soc - start_soc
                
                # Cập nhật SOH với Moving Average (5 lần gần nhất)
                if charge_energy > 0 and delta_soc >= 10.0:
                    real_capacity = (charge_energy * 0.92) / (delta_soc / 100.0) # Sạc lưới hiệu suất 92%
                    soh_calc = (real_capacity / cap) * 100.0
                    if 50.0 <= soh_calc <= 110.0:
                        if getattr(self, '_soh_history', None) is None: self._soh_history = []
                        if len(self._soh_history) == 0 or abs(self._soh_history[-1] - soh_calc) > 0.1:
                            self._soh_history.append(soh_calc)
                            if len(self._soh_history) > 5: self._soh_history.pop(0)
                            
                if getattr(self, '_soh_history', None) and len(self._soh_history) > 0:
                    avg_soh = sum(self._soh_history) / len(self._soh_history)
                    self._last_data["api_soh_calculated"] = round(min(avg_soh, 100.0), 1)
                else:
                    soh_raw = safe_float(self._last_data.get("34220_00001_00001", 100))
                    self._last_data["api_soh_calculated"] = round(soh_raw, 1)
                    
            batt_pct = safe_float(self._last_data.get("34183_00001_00009", self._last_data.get("34180_00001_00011", 0)))
            calc_max = safe_float(self._last_data.get("api_calc_max_range", 0))
            soh = safe_float(self._last_data.get("api_soh_calculated", 100))
            
            # Tính Remaining Capacity (Dung lượng pin khả dụng)
            if cap > 0:
                remain_cap = cap * (soh / 100.0) * (batt_pct / 100.0)
                self._last_data["api_remaining_capacity"] = round(remain_cap, 2)
            
            if safe_float(self._last_data.get("api_calc_range_per_percent", 0)) == 0.0:
                if calc_max > 0:
                    self._last_data["api_calc_range_per_percent"] = round(calc_max / 100.0, 2)
                elif ran > 0:
                    self._last_data["api_calc_range_per_percent"] = round(ran / 100.0, 2)

            rpp = safe_float(self._last_data.get("api_calc_range_per_percent", 0))
            
            # Adaptive Range dựa trên lịch sử 3 chuyến gần nhất
            adaptive_rpp = rpp
            if getattr(self, '_trip_efficiency_history', None) and len(self._trip_efficiency_history) > 0:
                adaptive_rpp = sum(self._trip_efficiency_history) / len(self._trip_efficiency_history)
            
            if rpp > 0 and batt_pct > 0:
                self._last_data["api_calc_remain_range"] = round(rpp * batt_pct, 1)
                self._last_data["api_adaptive_range"] = round(adaptive_rpp * batt_pct, 1)

            cost_per_kwh = safe_float(self.options.get("cost_per_kwh", 4000))
            gas_price = safe_float(self.options.get("gas_price", 20000))
            gas_km_per_liter = getattr(self, 'gas_km_per_liter', 15.0)

            total_kwh_charged = safe_float(self._last_data.get("api_total_energy_charged", 0))
            self._last_data["api_total_charge_cost_est"] = round(total_kwh_charged * cost_per_kwh)

            odo = safe_float(self._last_data.get("34183_00001_00003", self._last_data.get("34199_00000_00000", 0)))
            if odo > 0 and gas_km_per_liter > 0:
                self._last_data["api_total_gas_cost"] = round((odo / gas_km_per_liter) * gas_price)

            # Tính toán Thống kê trong ngày (Daily Stats)
            import datetime as dt_module
            now = dt_module.datetime.now()
            current_date_str = now.strftime("%Y-%m-%d")
            now_ts = time.time()
            is_active = getattr(self, '_is_trip_active', False)

            daily_date = self._last_data.get("api_daily_date", "")
            if not daily_date:
                self._last_data["api_daily_date"] = current_date_str
                daily_date = current_date_str

            if daily_date != current_date_str:
                if is_active:
                    self._pending_daily_rollover_date = current_date_str
                elif not getattr(self, '_daily_rollover_after_ts', 0) or now_ts >= getattr(self, '_daily_rollover_after_ts', 0):
                    self._last_data["api_daily_date"] = current_date_str
                    self._last_data["api_daily_distance_history"] = 0.0
                    self._last_data["api_daily_energy_history"] = 0.0
                    self._pending_daily_rollover_date = None
                    self._daily_rollover_after_ts = 0

            daily_dist = safe_float(self._last_data.get("api_daily_distance_history", 0))
            daily_energy = safe_float(self._last_data.get("api_daily_energy_history", 0))

            # Active trip chỉ là preview; không cộng dồn lặp lại mỗi lần poll.
            active_dist = 0.0
            active_energy = 0.0
            if is_active:
                start_date_str = dt_module.datetime.fromtimestamp(getattr(self, '_trip_start_time', now_ts)).strftime("%Y-%m-%d")
                if start_date_str == self._last_data.get("api_daily_date", current_date_str):
                    active_dist = getattr(self, '_trip_accumulated_distance_m', 0.0) / 1000.0
                    start_soc = getattr(self, '_trip_start_soc', 0)
                    current_soc = safe_float(self._last_data.get("34183_00001_00009", self._last_data.get("34180_00001_00011", 0)))
                    if cap > 0 and start_soc > current_soc:
                        active_energy = ((start_soc - current_soc) / 100.0) * cap

            self._last_data["api_daily_distance"] = round(daily_dist + active_dist, 2)
            self._last_data["api_daily_energy"] = round(daily_energy + active_energy, 2)

        except Exception:
            _LOGGER.exception("VinFast: không thể tính advanced statistics")

    async def async_smooth_trip_background(self, trip_id, raw_route, target_trip_file=None):
        """Compatibility no-op. Canonical routes are immutable raw GPS."""
        # [2.9.54] WARNING -> DEBUG: hàm no-op tương thích, không phải vấn đề.
        _LOGGER.debug("VinFast: [TRIP-SMOOTH-DISABLED] trip_id=%s points=%s", trip_id, len(raw_route or []))
        return False


    async def async_fix_all_historical_trips(self, force=False):
        """Compatibility no-op. Historical routes are never rewritten."""
        _LOGGER.info("VinFast: historical route transformation disabled")
        return 0

    async def _load_state(self):
        """Load persisted state from disk without blocking the event loop."""
        if not self.vin:
            return
        loop = asyncio.get_event_loop()
        # Tự động migrate dữ liệu cũ từ www/ sang .storage/vinfast/ nếu cần
        await loop.run_in_executor(None, self._migrate_old_data)
        await loop.run_in_executor(None, self._load_state_sync)
        # Post-load fixups that must run in the event loop
        vn = str(self._last_data.get("api_vehicle_name", ""))
        if vn.lower() in ["0", "1", "unknown", "none", "", "vinfast"]:
            self._last_data["api_vehicle_name"] = self.vehicle_model_display or "Xe VinFast"
            
        # Force geocoding if address is missing or "Đang tải" after load
        curr_addr = self._last_data.get("api_current_address", "")
        import logging
        _GEO_LOG = logging.getLogger(__name__)
        _GEO_LOG.debug(f"VinFast: [LOAD-GEO] curr_addr='{curr_addr}'")
        if any(kw in curr_addr for kw in ["Tọa độ", "Đang kết nối", "Loading", "Đang tải", "--"]) or not curr_addr:
            lat = safe_float(self._last_data.get("api_last_lat"), 0.0)
            lon = safe_float(self._last_data.get("api_last_lon"), 0.0)
            _GEO_LOG.debug(f"VinFast: [LOAD-GEO] Triggers geocoding with lat={lat}, lon={lon}, has_mqtt={hasattr(self, 'mqtt')}")
            if lat > 0 and lon > 0 and hasattr(self, 'mqtt'):
                self.hass.async_create_task(self.mqtt._update_location_async(lat, lon))

        # GPS history is canonical raw data. Never auto-transform it on startup.


    def _migrate_old_data(self):
        """Tự động migrate dữ liệu JSON từ thư mục www/ sang .storage/vinfast/ (chạy 1 lần)."""
        try:
            import glob as _glob, shutil as _shutil
            # Xác định đường dẫn www/ tương đối so với storage_dir
            new_dir = self.storage_dir
            # Tìm thư mục www/ của HA
            ha_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            old_dir = os.path.join(ha_config_dir, "www")
            if not os.path.isdir(old_dir):
                return
            vin_lower = self.vin.lower()
            patterns = [
                f"vinfast_state_{vin_lower}.json",
                f"vinfast_charge_history_{vin_lower}.json",
                f"vinfast_changelog_{vin_lower}.json",
                f"vinfast_trips_{vin_lower}.json",
            ] + _glob.glob(os.path.join(old_dir, f"vinfast_trips_archive_{vin_lower}_*.json"))
            
            for src_name in patterns:
                if isinstance(src_name, str) and not src_name.startswith("/"):
                    src = os.path.join(old_dir, src_name)
                else:
                    src = src_name  # full path từ glob
                    src_name = os.path.basename(src)
                
                if not os.path.exists(src):
                    continue
                dst = os.path.join(new_dir, src_name)
                if os.path.exists(dst):
                    # So sánh thời gian: chỉ copy nếu file cũ mới hơn file đích
                    if os.path.getmtime(src) <= os.path.getmtime(dst):
                        continue
                try:
                    _shutil.copy2(src, dst)
                    _LOGGER.info(f"VinFast: [MIGRATE] ✅ Đã chuyển {src_name} → .storage/vinfast/")
                except Exception as me:
                    _LOGGER.warning(f"VinFast: [MIGRATE] ⚠️ Không thể copy {src_name}: {me}")
        except Exception as e:
            _LOGGER.debug(f"VinFast: [MIGRATE] Bỏ qua migration: {e}")


    def _load_state_sync(self):
        """Blocking file I/O for loading state – run inside an executor."""
        if not self.vin: return
        state_file = os.path.join(self.storage_dir, f"vinfast_state_{self.vin.lower()}.json")
        charge_history_file = os.path.join(self.storage_dir, f"vinfast_charge_history_{self.vin.lower()}.json")
        if os.path.exists(charge_history_file):
            try:
                with open(charge_history_file, 'r', encoding='utf-8') as f:
                    ch_data = json.load(f)
                # Format mới: dict với metadata + sessions
                if isinstance(ch_data, dict) and "sessions" in ch_data:
                    sessions = ch_data.get("sessions", [])
                    metadata = ch_data.get("metadata", {})
                    # Lấy tổng kWh từ metadata (đã tổng hợp toàn bộ lịch sử)
                    cached_total_kwh = float(metadata.get("total_kwh", 0))
                    if cached_total_kwh > 0:
                        self._last_data["api_total_energy_charged"] = cached_total_kwh
                    # Chỉ đẩy 20 phiên gần nhất lên UI
                    self._last_data["api_charge_history_list"] = json.dumps(sessions[:20], ensure_ascii=False)
                    _LOGGER.info(f"VinFast: [STARTUP] Đã nạp cache {len(sessions)} phiên sạc, total_kwh={cached_total_kwh:.1f} kWh")
                # Format cũ: list thuần
                elif isinstance(ch_data, list):
                    self._last_data["api_charge_history_list"] = json.dumps(ch_data)
                    # Tổng hợp kWh từ list cũ làm tạm
                    partial_kwh = sum(float(s.get("kwh", 0)) for s in ch_data)
                    if partial_kwh > 0:
                        self._last_data["api_total_energy_charged"] = partial_kwh
            except Exception as e:
                _LOGGER.warning(f"VinFast: [STARTUP] Lỗi đọc charge cache: {e}")
        
        # Load driving trend cache (xu hướng lái xe)
        trend_cache_file = os.path.join(self.storage_dir, f"vinfast_driving_trend_{self.vin.lower()}.json")
        if os.path.exists(trend_cache_file):
            try:
                with open(trend_cache_file, 'r', encoding='utf-8') as f:
                    trend_data = json.load(f)
                trends = trend_data.get("trends", {})
                if trends:
                    self._last_data["api_driving_trend_json"] = json.dumps(trends, ensure_ascii=False)
                    # Tính lifetime efficiency từ cache 365 ngày
                    for period in ["365", "30", "7"]:
                        if period in trends:
                            eff = trends[period].get("efficiency_kwh_100km")
                            if eff and 5.0 <= eff <= 40.0:
                                if period == "365":
                                    current_eff = float(self._last_data.get("api_lifetime_efficiency", 0))
                                    if current_eff == 0 or current_eff == 15.0:
                                        self._last_data["api_lifetime_efficiency"] = eff
                                break
                    _LOGGER.info(f"VinFast: [STARTUP] Đã nạp cache xu hướng lái xe ({len(trends)} kỳ)")
            except Exception as e:
                _LOGGER.warning(f"VinFast: [STARTUP] Lỗi đọc driving trend cache: {e}")

        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    if "last_data" in saved_data: self._last_data.update(saved_data["last_data"])
                    if "internal_memory" in saved_data:
                        mem = saved_data["internal_memory"]
                        self._is_trip_active = mem.get("is_trip_active", False)
                        self._trip_start_odo = mem.get("trip_start_odo", 0.0)
                        self._trip_start_time = mem.get("trip_start_time", time.time())
                        self._trip_start_soc = mem.get("trip_start_soc", 100.0)
                        self._trip_accumulated_distance_m = mem.get("trip_accumulated_distance_m", 0.0)
                        self._route_coords = mem.get("route_coords", [])
                        self._last_gps_time = mem.get("last_gps_time", time.time())
                        self._last_ai_anomaly_time = mem.get("last_ai_anomaly_time", 0)
                        self._last_ai_weather_time = mem.get("last_ai_weather_time", 0)
                        self._is_parked = mem.get("is_parked", False)
                        self._parked_since = mem.get("parked_since")
                        self._last_lat_lon = mem.get("last_lat_lon", "")

                        self._eff_initial_soc = mem.get("eff_initial_soc", None)
                        self._eff_start_soc = mem.get("eff_start_soc", None)
                        self._eff_gps_dist = mem.get("eff_gps_dist", 0.0)
                        self._eff_ignored_first = mem.get("eff_ignored_first", False)

                        self._charge_start_soc = mem.get("charge_start_soc", 0.0)
                        self._charge_calc_soc = mem.get("charge_calc_soc", 0.0)
                        self._charge_start_time = mem.get("charge_start_time", time.time())
                        self._charge_calc_time = mem.get("charge_calc_time", time.time())
                        self._is_charging = mem.get("is_charging", False)
                        self._last_is_charging = mem.get("last_is_charging", False)
                        self._current_charge_max_power = mem.get("current_charge_max_power", 0.0)

                        self._since_charge_start_odo = mem.get("since_charge_start_odo", None)
                        self._since_charge_start_soc = mem.get("since_charge_start_soc", None)
                        self._soh_history = mem.get("soh_history", [])
                        self._live_charge_power_history = mem.get("live_charge_power_history", [])
                        self._trip_efficiency_history = mem.get("trip_efficiency_history", [])

                        lat_start = self._last_data.get("api_last_lat")
                        lon_start = self._last_data.get("api_last_lon")
                        if lat_start and lon_start: self._last_lat_lon = f"{lat_start},{lon_start}"
            except Exception:
                _LOGGER.exception("VinFast: không thể khôi phục runtime state")

    def _atomic_json_write(self, path, data):
        """Write JSON atomically; preserve the old file on failure."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            try:
                dir_fd = os.open(os.path.dirname(path), os.O_RDONLY)
                try: os.fsync(dir_fd)
                finally: os.close(dir_fd)
            except OSError:
                pass
        except Exception:
            try: os.unlink(tmp)
            except OSError: pass
            raise

    def _save_state(self):
        if not self.vin: return False
        os.makedirs(self.storage_dir, exist_ok=True)
        state_file = os.path.join(self.storage_dir, f"vinfast_state_{self.vin.lower()}.json")
        changelog_file = os.path.join(self.storage_dir, f"vinfast_changelog_{self.vin.lower()}.json")
        www_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "www"))
        www_state_file = os.path.join(www_dir, f"vinfast_state_{self.vin.lower()}.json") if os.path.isdir(www_dir) else None
        www_changelog_file = os.path.join(www_dir, f"vinfast_changelog_{self.vin.lower()}.json") if os.path.isdir(www_dir) else None
        try:
            self._last_data["api_debug_raw_json"] = json.dumps(self._raw_json_dict) if getattr(self, '_raw_json_dict', {}) else "{}"
            data_to_save = {"last_data": self._last_data.copy(), "internal_memory": {
                "is_trip_active": getattr(self, '_is_trip_active', False),
                "trip_start_odo": getattr(self, '_trip_start_odo', 0.0),
                "trip_start_time": getattr(self, '_trip_start_time', time.time()),
                "trip_start_soc": getattr(self, '_trip_start_soc', 100.0),
                "trip_accumulated_distance_m": getattr(self, '_trip_accumulated_distance_m', 0.0),
                "route_coords": getattr(self, '_route_coords', []),
                "last_gps_time": getattr(self, '_last_gps_time', time.time()),
                "last_ai_anomaly_time": getattr(self, '_last_ai_anomaly_time', 0),
                "last_ai_weather_time": getattr(self, '_last_ai_weather_time', 0),
                "is_parked": getattr(self, '_is_parked', False),
                "parked_since": getattr(self, '_parked_since', None),
                "last_lat_lon": getattr(self, '_last_lat_lon', ""),
                "eff_initial_soc": getattr(self, '_eff_initial_soc', None), "eff_start_soc": getattr(self, '_eff_start_soc', None),
                "eff_gps_dist": getattr(self, '_eff_gps_dist', 0.0), "eff_ignored_first": getattr(self, '_eff_ignored_first', False),
                "charge_start_soc": getattr(self, '_charge_start_soc', 0.0), "charge_calc_soc": getattr(self, '_charge_calc_soc', 0.0),
                "charge_start_time": getattr(self, '_charge_start_time', time.time()), "charge_calc_time": getattr(self, '_charge_calc_time', time.time()),
                "is_charging": getattr(self, '_is_charging', False), "last_is_charging": getattr(self, '_last_is_charging', False),
                "current_charge_max_power": getattr(self, '_current_charge_max_power', 0.0),
                "since_charge_start_odo": getattr(self, '_since_charge_start_odo', None), "since_charge_start_soc": getattr(self, '_since_charge_start_soc', None),
                "soh_history": getattr(self, '_soh_history', []), "live_charge_power_history": getattr(self, '_live_charge_power_history', []),
                "trip_efficiency_history": getattr(self, '_trip_efficiency_history', [])}, "unix_time": time.time()}
            with self._file_lock:
                self._atomic_json_write(state_file, data_to_save)
                if www_state_file: self._atomic_json_write(www_state_file, data_to_save)
                if hasattr(self, '_changelog_buffer') and self._changelog_buffer:
                    old_changelog = []
                    if os.path.exists(changelog_file):
                        with open(changelog_file, encoding='utf-8') as cf: old_changelog = json.load(cf)
                    merged_log = (self._changelog_buffer + old_changelog)[:100]
                    self._atomic_json_write(changelog_file, merged_log)
                    if www_changelog_file: self._atomic_json_write(www_changelog_file, merged_log)
                    self._changelog_buffer = []
            return True
        except Exception as exc:
            _LOGGER.error("VinFast: [STATE-SAVE] durable save failed; state retained: %s", exc)
            return False

    def _save_trip_history(self):
        if not self.vin: return
        try:
            import datetime
            os.makedirs(self.storage_dir, exist_ok=True)
            trip_file = os.path.join(self.storage_dir, f"vinfast_trips_{self.vin.lower()}.json")
            
            # Cũng ghi sang www/ để JS card cũ vẫn đọc được (BACKWARD COMPAT)
            www_trip_file = None
            try:
                ha_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                www_dir = os.path.join(ha_config_dir, "www")
                if os.path.isdir(www_dir):
                    www_trip_file = os.path.join(www_dir, f"vinfast_trips_{self.vin.lower()}.json")
            except Exception:
                pass
            
            with self._file_lock:
                if os.path.exists(trip_file):
                    with open(trip_file, 'r', encoding='utf-8') as f: trips = json.load(f)
                    if not isinstance(trips, list): raise ValueError("trip history schema invalid")
                elif www_trip_file and os.path.exists(www_trip_file):
                    with open(www_trip_file, 'r', encoding='utf-8') as f: trips = json.load(f)
                    if not isinstance(trips, list): raise ValueError("trip history schema invalid")
                    # [2.9.54] WARNING -> DEBUG: đọc từ www/ là fallback bình thường.
                    _LOGGER.debug(f"VinFast: [TRIP-SAVE] Đọc trips từ www/ (fallback): {len(trips)} chuyến")
                else:
                    trips = []
                
                dist = float(self._last_data.get("api_trip_distance", 0))
                route_count = len(self._route_coords)
                # [2.9.54] WARNING -> INFO: sự kiện vòng đời bình thường.
                _LOGGER.info(f"VinFast: [TRIP-SAVE] Bắt đầu lưu chuyến: dist={dist:.2f}km route_pts={route_count} trip_file={trip_file}")
                
                if dist > 0.05 or route_count > 2: 
                    start_dt = datetime.datetime.fromtimestamp(self._trip_start_time)
                    end_ts = getattr(self, '_parked_since', None) or time.time()
                    end_dt = datetime.datetime.fromtimestamp(end_ts)
                    dur_mins = int((end_dt.timestamp() - self._trip_start_time) / 60)
                    start_addr = f"{self._route_coords[0][0]}, {self._route_coords[0][1]}" if self._route_coords else "Unknown"
                    end_addr = f"{self._route_coords[-1][0]}, {self._route_coords[-1][1]}" if self._route_coords else "Unknown"
                    
                    trip_id = int(end_dt.timestamp())
                    
                    # Raw route lưu nguyên — không drop điểm bằng moving_average/RDP
                    # Smooth riêng được ghi qua TripStorageManager daily files
                    draft_route = list(self._route_coords)
                    
                    # Tính toán năng lượng tiêu thụ
                    trip_start_soc = getattr(self, '_trip_start_soc', 0.0)
                    current_soc = safe_float(self._last_data.get("34183_00001_00009", 0.0))
                    cap = safe_float(self._last_data.get("api_static_capacity", 18.64))
                    if cap == 0: cap = 18.64
                    soh = safe_float(self._last_data.get("api_soh_calculated", 100.0))
                    if soh <= 0 or soh > 100: soh = 100.0
                    
                    # Phương pháp 1: Tính dựa trên % pin (SOC) và độ hao mòn (SOH)
                    energy_from_soc = 0.0
                    if trip_start_soc > current_soc:
                        energy_from_soc = ((trip_start_soc - current_soc) / 100.0) * (cap * (soh / 100.0))
                        
                    # Phương pháp 2: Tính dựa trên trung bình điện năng đã sạc và quãng đường
                    total_energy_charged = safe_float(self._last_data.get("api_total_energy_charged", 0.0))
                    current_odo = safe_float(self._last_data.get("34183_00001_00003", safe_float(self._last_data.get("34199_00000_00000", 0.0))))
                    energy_from_charge = 0.0
                    if total_energy_charged > 0 and current_odo > 0:
                        lifetime_efficiency = total_energy_charged / (current_odo / 100.0)
                        if 5.0 <= lifetime_efficiency <= 40.0: # Lọc các giá trị vô lý
                            energy_from_charge = (dist / 100.0) * lifetime_efficiency
                            
                    # Phương pháp 3: Dùng api_lifetime_efficiency (từ driving trend API hoặc tính toán)
                    energy_from_api = safe_float(self._last_data.get("api_trip_energy_used", 0.0))
                    lifetime_eff_sensor = safe_float(self._last_data.get("api_lifetime_efficiency", 0.0))
                    energy_from_lifetime_eff = 0.0
                    if lifetime_eff_sensor > 0 and lifetime_eff_sensor != 15.0 and dist > 0:
                        energy_from_lifetime_eff = (dist / 100.0) * lifetime_eff_sensor
                    
                    # Lấy trung bình cộng của các phương pháp hợp lệ
                    valid_energies = []
                    if energy_from_soc > 0.05: valid_energies.append(energy_from_soc)
                    if energy_from_charge > 0.05: valid_energies.append(energy_from_charge)
                    
                    if len(valid_energies) > 0:
                        final_energy = sum(valid_energies) / len(valid_energies)
                    elif energy_from_api > 0:
                        final_energy = energy_from_api
                    elif energy_from_lifetime_eff > 0:
                        final_energy = energy_from_lifetime_eff  # Dùng hiệu suất thực thay vì hardcode
                    else:
                        final_energy = 0.0  # Để 0 thay vì hardcode 15.0 - sẽ được fallback trên JS bằng lifetime efficiency thực

                    
                    new_trip = {
                        "id": trip_id,
                        "session_id": trip_id,
                        "timestamp": trip_id,
                        "start_timestamp": int(self._trip_start_time),
                        "end_timestamp": int(end_ts),
                        "date": start_dt.strftime("%d/%m/%Y"),
                        "start_time": start_dt.strftime("%H:%M"),
                        "end_time": end_dt.strftime("%H:%M"),
                        "duration": dur_mins if dur_mins > 0 else 1,
                        "distance": round(dist, 2),
                        "energy_used": round(final_energy, 2),
                        "start_address": start_addr,
                        "end_address": end_addr,
                        "route": draft_route,
                        "raw_route": list(self._route_coords),
                        "is_smoothed": False,
                    }
                    trips = [
                        t for t in trips
                        if not isinstance(t, dict)
                        or t.get("session_id") != new_trip["session_id"]
                        and t.get("id") != new_trip["id"]
                    ]
                    trips.insert(0, new_trip)
                    committed = trips[:1000]
                    self._atomic_json_write(trip_file, committed)
                    if www_trip_file: self._atomic_json_write(www_trip_file, committed)
                    # [2.9.54] WARNING -> INFO: lưu thành công là chuyện thường.
                    _LOGGER.info(f"VinFast: [TRIP-SAVE] ✅ Durable commit: {trip_file} (tổng {len(committed)} chuyến, points={len(draft_route)})")
                    return True
                # [2.9.54] WARNING -> DEBUG: chuyến quá ngắn thì bỏ qua là bình thường.
                _LOGGER.debug(f"VinFast: [TRIP-SAVE] Bỏ qua lưu: dist={dist:.2f}km route_pts={route_count} (quá ngắn)")
                return True
        except Exception as e:
            _LOGGER.error(f"VinFast: [TRIP-SAVE] Durable commit failed; route retained: {e}")
            return False

    @property
    def storage_dir(self):
        if hasattr(self, 'hass') and self.hass:
            path = self.hass.config.path(".storage", "vinfast")
            os.makedirs(path, exist_ok=True)
            return path
        fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".storage", "vinfast"))
        os.makedirs(fallback_path, exist_ok=True)
        return fallback_path
