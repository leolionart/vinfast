import json
import time
import datetime
import logging
import uuid
import random
import math
import asyncio
import inspect
import os
import paho.mqtt.client as mqtt

from .const import WWW_DIR, MOCK_FILE, REGION_CONFIG, emqx_server
from .api_auth import normalize_iot_provider
from .api_helpers import async_get_address_from_osm, async_get_weather_data, async_get_osrm_route, collect_gps_pair, gps_distance_m, merge_routed_gap, route_gap_needs_repair, safe_float
from .ai_gemini import async_get_ai_advice
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


def _schedule_save_state(core):
    """Lưu state NGAY, gọi được từ thread paho-mqtt (không phải event loop).

    [2.9.51] FIX LỖI "RuntimeError: no running event loop" (92 lần / 175 phút).

    Code cũ ở 4 chỗ (trip-start, charge-start, giữa phiên sạc, kết thúc phiên sạc) gọi:
        asyncio.run_coroutine_threadsafe(
            core.hass.async_add_executor_job(core._save_state), core.hass.loop)
    Nhưng `HomeAssistant.async_add_executor_job` là @callback ĐỒNG BỘ (homeassistant/core.py:871),
    KHÔNG phải coroutine: nó chạy NGAY tại chỗ gọi, và bên trong gọi `asyncio.current_task()`
    (core.py:877). Trong thread paho-mqtt không có event loop đang chạy -> RuntimeError.
    Hệ quả: khối `try` bị `except` nuốt, state KHÔNG được lưu, log đầy traceback giả.

    `hass.add_job()` mới là API thread-safe: nó call_soon_threadsafe() rồi đẩy hàm
    đồng bộ sang executor. Dùng được từ cả thread paho-mqtt lẫn event loop.
    """
    try:
        core.hass.add_job(core._save_state)
    except Exception:
        _LOGGER.debug("VinFast: không schedule được _save_state", exc_info=True)


class MQTTManager:
    def __init__(self, core):
        self.core = core
        self.client = None
        self._needs_mqtt_renew = False 
        self._mqtt_client_id_rand = "".join(random.choice("0123456789qwertyuiop") for _ in range(15))
        self._geocode_lock = asyncio.Lock()
        self._pending_gps = {}
        self._current_provider = normalize_iot_provider(getattr(self.core, "iot_provider", None)) or "AWS"
        self._provider_connected_time = time.time()
        self._last_provider_refresh = time.time()
        self._last_provider_message = 0
        self._provider_retry_delay = 300
        self._next_provider_probe = time.time() + 300

    def start(self):
        self.core._running = True
        self.core.hass.loop.create_task(self._api_polling_loop())
        self.core.hass.loop.create_task(self.core.auth.fetch_charging_history())

    def stop(self):
        if self.client:
            self.client.loop_stop()
            try: self.client.disconnect()
            except Exception:
                _LOGGER.debug("VinFast: MQTT disconnect failed", exc_info=True)

    async def _renew_aws_connection(self):
        await self._renew_connection()

    async def _renew_connection(self):
        try:
            if self.client:
                self.client.loop_stop()
                try: self.client.disconnect()
                except Exception:
                    _LOGGER.debug("VinFast: MQTT reconnect disconnect failed", exc_info=True)
                self.client = None 

            self._provider_connected_time = time.time()
            if self._current_provider == "EMQX":
                await self._connect_emqx()
            elif self._current_provider == "AWS":
                await self._connect_aws()
            else:
                raise ValueError(f"Unsupported IoT provider: {self._current_provider}")
            self._needs_mqtt_renew = False
        except Exception as e:
            _LOGGER.error(f"VinFast: Lỗi kết nối {self._current_provider} MQTT: {e}")

    async def _connect_emqx(self):
        import ssl
        try:
            creds = await self.core.auth.get_emqx_credentials()
            if not creds:
                _LOGGER.error("VinFast: Không lấy được chứng chỉ EMQX JWT!")
                return
            session_token = creds.get("sessionToken")
            if not session_token:
                _LOGGER.error("VinFast: Phản hồi EMQX không có sessionToken!")
                return

            client_id = f"Android_{self.core.vin}_{self._mqtt_client_id_rand}"
            try: self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            except AttributeError: self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

            user_email = getattr(self.core, "email", "") or getattr(self.core, "user_id", "") or ""
            self.client.username_pw_set(username=user_email, password=session_token)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # [2.9.60] host/port MQTT qua `emqx_server()` — ba tầng ưu tiên:
            #   1. người dùng nhập ở UI (Options: emqx_host / emqx_port)
            #   2. REGION_CONFIG trong const.py
            #   3. mặc định cứng (hành vi cũ)
            # Hai giá trị này KHÔNG endpoint nào trả về nên phải cấu hình được.
            _host, _port = emqx_server(getattr(self.core, "region", "VN"),
                                       getattr(self.core, "options", None))
            _LOGGER.info("VinFast: [CONST-SYNC] MQTT EMQX <- %s:%s (region=%s)",
                         _host, _port, getattr(self.core, "region", "VN"))
            def _setup_emqx():
                ssl_ctx = ssl.create_default_context()
                ca_path = os.path.join(os.path.dirname(__file__), "root_ca_prod.pem")
                if os.path.exists(ca_path):
                    try:
                        ssl_ctx.load_verify_locations(ca_path)
                    except Exception:
                        pass
                # VinFast internal EMQX cert lacks Authority Key Identifier; Python 3.14 requires CERT_NONE
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                self.client.tls_set_context(ssl_ctx)
                self.client.connect(_host, _port, 60)
                self.client.loop_start()

            if hasattr(self.core, 'hass') and self.core.hass:
                await self.core.hass.async_add_executor_job(_setup_emqx)
            else:
                _setup_emqx()
            _LOGGER.info("VinFast: 🌐 Khởi tạo kết nối EMQX MQTT (%s:%s) thành công!",
                         _host, _port)
        except Exception as e:
            _LOGGER.error(f"VinFast: Lỗi kết nối EMQX MQTT: {e}")

    async def _connect_aws(self):
        import hmac
        import urllib.parse
        import hashlib
        try:
            # Xin chứng chỉ AWS mới thông qua API UAA
            creds = await self.core.auth.get_aws_credentials()
            if not creds:
                _LOGGER.error("VinFast: Không lấy được chứng chỉ AWS IoT!")
                return
                
            access_key = creds.get("accessKeyId")
            secret_key = creds.get("secretKeyId")
            session_token = creds.get("sessionToken")

            t = datetime.datetime.now(datetime.timezone.utc)
            amz_date = t.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = t.strftime('%Y%m%d')

            def aws_sign(k, m): return hmac.new(k, m.encode('utf-8'), hashlib.sha256).digest()

            aws_region = self.core.aws_region
            iot_endpoint = self.core.iot_endpoint

            scope = f"{date_stamp}/{aws_region}/iotdevicegateway/aws4_request"
            qs = f"X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential={urllib.parse.quote(access_key + '/' + scope, safe='')}&X-Amz-Date={amz_date}&X-Amz-Expires=86400&X-Amz-SignedHeaders=host"
            sts = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n" + hashlib.sha256(f"GET\n/mqtt\n{qs}\nhost:{iot_endpoint}\n\nhost\n{hashlib.sha256(b'').hexdigest()}".encode('utf-8')).hexdigest()
            k_sign = aws_sign(aws_sign(aws_sign(aws_sign(f"AWS4{secret_key}".encode('utf-8'), date_stamp), aws_region), 'iotdevicegateway'), 'aws4_request')
            signature = hmac.new(k_sign, sts.encode('utf-8'), hashlib.sha256).hexdigest()

            url = f"wss://{iot_endpoint}/mqtt?{qs}&X-Amz-Signature={signature}&X-Amz-Security-Token={urllib.parse.quote(session_token, safe='')}"

            client_id = f"Android_{self.core.vin}_{self._mqtt_client_id_rand}"
            try: self.client = mqtt.Client(client_id=client_id, transport="websockets", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            except AttributeError: self.client = mqtt.Client(client_id=client_id, transport="websockets")

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            def _setup_mqtt():
                self.client.tls_set()
                self.client.ws_set_options(path=url.split(iot_endpoint)[1])
                self.client.connect(iot_endpoint, 443, 60)
                self.client.loop_start()
                
            if hasattr(self.core, 'hass') and self.core.hass:
                await self.core.hass.async_add_executor_job(_setup_mqtt)
            else:
                _setup_mqtt()
            _LOGGER.info("VinFast: 🌐 Khởi tạo kết nối AWS IoT WSS MQTT thành công!")
        except Exception as e:
            _LOGGER.error(f"VinFast: Lỗi kết nối AWS MQTT: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            now = time.time()
            self._provider_connected_time = now
            _LOGGER.info(f"VinFast: Provider {self._current_provider} MQTT đã kết nối")
            client.subscribe(f"/mobile/{self.core.vin}/push", qos=1)
            client.subscribe(f"monitoring/server/{self.core.vin}/push", qos=1)
            client.subscribe(f"control/server/{self.core.vin}/push", qos=1)
            client.subscribe(f"/server/{self.core.vin}/remctrl", qos=1)
            self.core._last_mqtt_msg_time = now
            if hasattr(self.core, 'hass') and self.core.hass:
                asyncio.run_coroutine_threadsafe(self.core.auth.register_resources(), self.core.hass.loop)

    def _on_disconnect(self, client, userdata, *args, **kwargs):
        self._needs_mqtt_renew = True

    def _send_heartbeat(self, state=None):
        if not self.client or not self.client.is_connected() or not self.core.vin: return
        topic = f"/vehicles/{self.core.vin}/push/connected/heartbeat"
        if state is None:
            if self._current_provider == "EMQX":
                hb_val = "CONNECTED"
            else:
                hb_val = "2" if getattr(self.core, '_is_moving', False) else "1"
        else:
            hb_val = str(state)
        payload = {"version": "1.2", "timestamp": int(time.time() * 1000), "trans_id": str(uuid.uuid4()), "content": {"34183": { "1": { "54": hb_val } }}}
        try: self.client.publish(topic, json.dumps(payload), qos=1)
        except Exception:
            _LOGGER.exception("VinFast: lỗi parse MQTT payload")

    async def _api_polling_loop(self):
        await asyncio.sleep(5) 
        if not self.core.user_id: await self.core.auth.get_vehicles()
        discovered_provider = normalize_iot_provider(getattr(self.core, "iot_provider", None))
        if discovered_provider:
            self._current_provider = discovered_provider
        await self._renew_connection()
        await self.core.auth.register_resources()
        
        last_heartbeat = time.time()
        last_state_save = time.time()
        last_aws_renew = time.time()
        
        _last_debug_log = 0  # DEBUG: Timer log trạng thái trip
        while self.core._running:
            try:
                await asyncio.sleep(1)
                now = time.time()
                core = self.core

                if now - last_heartbeat >= 25:
                    last_heartbeat = now
                    self._send_heartbeat()

                if now - last_aws_renew >= 3000 or self._needs_mqtt_renew:
                    last_aws_renew = now
                    await self._renew_connection()

                # The account API is authoritative during VinFast's staged migrations.
                if now - self._last_provider_refresh >= 900:
                    self._last_provider_refresh = now
                    discovered_provider = await core.auth.refresh_iot_provider()
                    if discovered_provider and discovered_provider != getattr(core, "iot_provider", None):
                        old_provider = self._current_provider
                        self._current_provider = discovered_provider
                        core.iot_provider = discovered_provider
                        _LOGGER.info(
                            "VinFast: Server đổi provider %s -> %s; kết nối lại",
                            old_provider, discovered_provider,
                        )
                        await self._renew_connection()

                time_since_last_msg = now - getattr(core, '_last_mqtt_msg_time', now)
                time_on_provider = now - self._provider_connected_time

                # Retry the other supported transport only after a full no-data interval.
                if time_since_last_msg >= 300 and time_on_provider >= 300 and now >= self._next_provider_probe:
                    old_provider = self._current_provider
                    self._current_provider = "AWS" if old_provider == "EMQX" else "EMQX"
                    self._next_provider_probe = now + self._provider_retry_delay
                    self._provider_retry_delay = min(self._provider_retry_delay * 2, 1800)
                    _LOGGER.warning(
                        "VinFast: [FALLBACK] 300s không có MQTT data trên %s; thử %s (lần kế tiếp sau %ss)",
                        old_provider, self._current_provider, int(self._next_provider_probe - now),
                    )
                    core._last_mqtt_msg_time = now
                    await self._renew_connection()

                # [2.9.56] Xe đỗ lâu -> TCU ngủ -> MQTT im lặng và ping 403, nên toạ độ
                # không bao giờ về. Chủ động gọi endpoint wakeup, rồi ping lại nhanh trong
                # cửa sổ wakeup để bắt đúng lúc xe vừa thức và bắt đầu đẩy dữ liệu.
                wakeup_window = now < getattr(core.auth, "_wakeup_ping_until", 0)
                if wakeup_window:
                    if now - getattr(self, "_last_wakeup_ping", 0) >= 20:
                        self._last_wakeup_ping = now
                        await core.auth.register_resources(force=True)
                else:
                    has_position = core._last_data.get("api_last_lat") is not None
                    if (
                        time_since_last_msg >= 300
                        and not has_position
                        and not getattr(core, "_is_moving", False)
                        and now - getattr(self, "_last_wakeup_request", 0) >= 300
                    ):
                        self._last_wakeup_request = now
                        await core.auth.wake_vehicle()

                if getattr(core, '_is_moving', False) and time_since_last_msg > 180:
                    self._needs_mqtt_renew = True
                    core._last_mqtt_msg_time = now 

                if getattr(core, '_is_charging', False):
                    if now - getattr(self, '_last_active_charge_fetch', 0) >= 60:
                        self._last_active_charge_fetch = now
                        has_api_power = core.auth.fetch_active_charging_session()
                        if inspect.isawaitable(has_api_power):
                            has_api_power = await has_api_power
                        if has_api_power:
                            core._last_api_power_time = now 
                        core.trigger_callbacks()

                if getattr(core, '_vehicle_offline', False):
                    time_since_last_wakeup = now - getattr(core, '_last_auto_wakeup_time', 0)
                    if time_since_last_wakeup > 180:
                        await core.auth.register_resources() 

                # [2.9.52] Làm tươi nhóm key "THEO THAY ĐỔI" (vị trí cần số, ODO, SOC,
                # quãng đường) khi xe đang chạy. T-Box chỉ đẩy nhóm này khi giá trị ĐỔI,
                # nên có thể im lặng suốt chuyến đi (đo được: gear không hề xuất hiện trên
                # MQTT trong 240 s). Response của ping luôn có giá trị mới nhất của server
                # -> gọi 120 s/lần khi đang di chuyển, rất rẻ (0,25 s/lần).
                if getattr(core, '_is_moving', False) or getattr(core, '_is_trip_active', False):
                    if now - getattr(self, '_last_move_telemetry_refresh', 0) >= 120:
                        self._last_move_telemetry_refresh = now
                        await core.auth.register_resources()

                if now - getattr(self, '_last_periodic_station_fetch', 0) >= 900:
                    self._last_periodic_station_fetch = now
                    core.hass.async_create_task(core.auth.fetch_nearby_stations(force=True))

                # DEBUG: Log trạng thái trip mỗi 30 giây
                if now - _last_debug_log >= 30:
                    _last_debug_log = now
                    route_pts = len(getattr(core, '_route_coords', []))
                    trip_dist = float(core._last_data.get('api_trip_distance', 0))
                    time_since_move = now - getattr(core, '_last_actual_move_time', now)
                    trip_active = getattr(core, '_is_trip_active', False)
                    is_moving = getattr(core, '_is_moving', False)
                    last_lat = core._last_data.get('api_last_lat', 0)
                    last_lon = core._last_data.get('api_last_lon', 0)
                    _LOGGER.debug(
                        f"VinFast: [TRIP-DEBUG] is_moving={is_moving} trip_active={trip_active} "
                        f"route_pts={route_pts} dist={trip_dist:.2f}km "
                        f"time_since_move={time_since_move:.0f}s lat={last_lat} lon={last_lon}"
                    )

                parked_since = getattr(core, '_parked_since', None)
                parked_for = now - parked_since if parked_since else 0
                if getattr(core, '_is_trip_active', False) and getattr(core, '_is_parked', False) and parked_for >= 300:
                    await self._repair_trip_route_gaps()
                    route_pts_count = len(getattr(core, '_route_coords', []))
                    trip_dist_end = float(core._last_data.get('api_trip_distance', 0))
                    # [2.9.54] WARNING -> INFO: sự kiện vòng đời bình thường.
                    _LOGGER.info(
                        f"VinFast: [TRIP-END] Kết thúc chuyến đi! dist={trip_dist_end:.2f}km "
                        f"route_pts={route_pts_count} parked_for={parked_for:.0f}s"
                    )
                    saved = await core.hass.async_add_executor_job(core._save_trip_history)
                    if not saved:
                        _LOGGER.error("VinFast: [TRIP-END] Save failed; active route retained for retry")
                        continue
                    core._is_trip_active = False
                    core._parked_since = None
                    if getattr(core, '_pending_daily_rollover_date', None):
                        core._daily_rollover_after_ts = time.time() + 300
                    
                    trip_dist = float(core._last_data.get("api_trip_distance", 0))
                    soc_start = getattr(core, '_trip_start_soc', 100.0)
                    soc_end = safe_float(core._last_data.get("34183_00001_00009", core._last_data.get("34180_00001_00011", 50)))
                    soc_drop = soc_start - soc_end
                    
                    # Cộng vào thống kê ngày (nếu chuyến đi bắt đầu trong ngày hôm nay)
                    import datetime as dt_module
                    start_date_str = dt_module.datetime.fromtimestamp(getattr(core, '_trip_start_time', time.time())).strftime("%Y-%m-%d")
                    current_date_str = dt_module.datetime.now().strftime("%Y-%m-%d")
                    if start_date_str == current_date_str:
                        core._last_data["api_daily_distance_history"] = float(core._last_data.get("api_daily_distance_history", 0)) + trip_dist
                        cap = float(core._last_data.get("api_static_capacity", 0))
                        if cap > 0 and soc_drop > 0:
                            core._last_data["api_daily_energy_history"] = float(core._last_data.get("api_daily_energy_history", 0)) + ((soc_drop / 100.0) * cap)

                    if getattr(core, '_pending_daily_rollover_date', None):
                        core._last_data["api_daily_date"] = core._pending_daily_rollover_date
                        core._last_data["api_daily_distance_history"] = 0.0
                        core._last_data["api_daily_energy_history"] = 0.0
                        core._pending_daily_rollover_date = None
                        core._daily_rollover_after_ts = 0

                    core._calculate_advanced_stats()
                    core._trip_start_odo = 0.0
                    core._trip_start_time = time.time()
                    core._route_coords = []
                    core._last_data["api_trip_route"] = "[]"
                    core._last_data["api_trip_distance"] = 0.0
                    core._last_data["api_trip_avg_speed"] = 0.0
                    core._last_data["api_trip_energy_used"] = 0.0
                    core._last_data["api_trip_efficiency"] = 0.0
                    core._trip_accumulated_distance_m = 0.0
                    _LOGGER.info("VinFast: [TRIP-END] Live trip state reset after durable commit")
                    await core.hass.async_add_executor_job(core._save_state)
                    core.trigger_callbacks()

                if now - last_state_save >= 60:
                    last_state_save = now
                    await core.hass.async_add_executor_job(core._save_state)
            except Exception as e:
                _LOGGER.error(f"VinFast: [POLLING-LOOP] Lỗi trong vòng lặp polling: {e}")

    async def _repair_trip_route_gaps(self):
        core = self.core
        route = list(getattr(core, '_route_coords', []))
        if len(route) < 2:
            return

        session = async_get_clientsession(core.hass)
        repaired = [route[0]]
        repaired_count = 0
        for before, after in zip(route, route[1:]):
            if route_gap_needs_repair(before, after) and repaired_count < 5:
                road = await async_get_osrm_route(session, before[0], before[1], after[0], after[1])
                direct_m = gps_distance_m(before[0], before[1], after[0], after[1])
                road_m = sum(gps_distance_m(*start, *end) for start, end in zip(road or [], (road or [])[1:]))
                if road_m and road_m <= min(50000.0, max(direct_m * 3.0, direct_m + 5000.0)):
                    repaired.extend(merge_routed_gap(before, after, road))
                    repaired_count += 1
                else:
                    _LOGGER.warning("VinFast: [TRIP-GAP] Không suy luận được đoạn %.0fm; UI sẽ tách đường", direct_m)
            repaired.append(after)

        if repaired_count:
            core._route_coords = repaired
            core._trip_accumulated_distance_m = sum(
                gps_distance_m(before[0], before[1], after[0], after[1])
                for before, after in zip(repaired, repaired[1:])
            )
            core._last_data["api_trip_route"] = json.dumps(repaired)
            core._last_data["api_trip_distance"] = round(core._trip_accumulated_distance_m / 1000.0, 2)
            # [2.9.54] WARNING -> INFO: tự phục hồi THÀNH CÔNG, không phải cảnh báo.
            _LOGGER.info("VinFast: [TRIP-GAP] Đã khôi phục %s đoạn thiếu bằng OSRM", repaired_count)

    async def _update_location_async(self, lat, lon):
        # [2.9.51] Hạ mức log: đây là log CHẨN ĐOÁN (216 dòng ERROR/3 giờ cho luồng bình thường)
        _LOGGER.debug(f"VinFast: [GEO-TEST] Bắt đầu _update_location_async lat={lat}, lon={lon}")
        try:
            core = self.core
            grid_coord = f"{round(float(lat), 3)},{round(float(lon), 3)}"
            curr_addr = core._last_data.get("api_current_address", "")
            
            # Fetch weather
            now = time.time()
            if now - getattr(core, '_last_weather_fetch_time', 0) >= 900:
                try:
                    session = async_get_clientsession(core.hass)
                    w_data = await async_get_weather_data(session, lat, lon)
                    if w_data:
                        core._last_weather_fetch_time = now
                        core._last_data["api_outside_temp"] = w_data["temp"]
                        core._last_data["api_weather_condition"] = w_data["condition"]
                        core._last_data["api_hvac_load_estimate"] = w_data["hvac"]
                        
                        bad_wmo_codes = [45, 48, 51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99]
                        is_bad_weather = w_data["code"] in bad_wmo_codes
                        is_extreme_temp = w_data["temp"] >= 35 or w_data["temp"] <= 15
                        cond_lower = str(w_data["condition"]).lower()
                        has_bad_keyword = any(k in cond_lower for k in ["mưa", "bão", "sương mù", "tuyết", "gió", "sấm chớp", "mù"])

                        if now - getattr(core, '_last_ai_weather_time', 0) > 21600 and (is_bad_weather or is_extreme_temp or has_bad_keyword):
                            core._last_ai_weather_time = now
                            core.hass.async_create_task(self._run_ai_advisor_wrapper("weather", {"temp": w_data["temp"], "cond": w_data["condition"]}))
                            
                        await core.hass.async_add_executor_job(core._save_state)
                        core.trigger_callbacks()
                except Exception as we:
                    # [2.9.51] ERROR -> WARNING: lỗi thời tiết không nghiêm trọng, có fallback
                    _LOGGER.warning(f"VinFast: [GEO-TEST] Lỗi lấy thời tiết: {we}")

                    
            async with self._geocode_lock:
                # FIX: Bổ sung "Đang tải" và "Loading" vào danh sách trigger geocoding
                _LOADING_KEYWORDS = ["Tọa độ", "Đang kết nối", "Loading", "Đang tải", "--"]
                needs_geocode = (
                    getattr(core, '_last_geocoded_grid', None) != grid_coord
                    or any(kw in curr_addr for kw in _LOADING_KEYWORDS)
                    or not curr_addr
                )
                if needs_geocode:
                    session = async_get_clientsession(core.hass)
                    _LOGGER.debug(f"VinFast: [GEO] Đang tra địa chỉ cho {lat:.5f},{lon:.5f}...")
                    addr = await async_get_address_from_osm(session, lat, lon)
                    if addr:
                        core._last_data["api_current_address"] = addr
                        core._last_geocoded_grid = grid_coord
                        _LOGGER.debug(f"VinFast: [GEO] ✅ Địa chỉ: {addr[:60]}")
                        core.hass.async_create_task(core.auth.fetch_nearby_stations(force=False))
                    else:
                        core._last_data["api_current_address"] = f"Lat/Lon: {lat:.5f}, {lon:.5f}"
                        _LOGGER.warning(f"VinFast: [GEO] ❌ Không tra được địa chỉ cho {lat:.5f},{lon:.5f}")
                    await core.hass.async_add_executor_job(core._save_state)
                    core.trigger_callbacks()
        except Exception as e:
            _LOGGER.warning(f"VinFast: [GEO] Lỗi cập nhật vị trí: {e}")

    async def _run_ai_advisor_wrapper(self, mode="trip", data_payload=None):
        core = self.core
        try:
            if mode not in ("weather", "anomaly"):
                return
            if not getattr(core, 'gemini_api_key', None) or core.gemini_api_key.strip() == "":
                return 
                
            std_range = safe_float(core._last_data.get("api_static_range", 210))
            expected_km_per_1 = round(std_range / 100.0, 2) if std_range > 0 else 2.1
            
            context_data = {
                "temp": core._last_data.get("api_outside_temp", "Unknown"),
                "cond": core._last_data.get("api_weather_condition", "Unknown"),
                "hvac": core._last_data.get("api_hvac_load_estimate", "Normal"),
                "expected_km_per_1": expected_km_per_1,
                "trip_dist": float(core._last_data.get("api_trip_distance", 0.0)),
                "trip_avg_speed": core._last_data.get("api_trip_avg_speed", 0)
            }
            
            ai_model = core.options.get("gemini_model", core.options.get("CONF_GEMINI_MODEL", "gemini-2.5-flash"))
            vi = core.lang == "vi"
            
            if mode == "weather":
                core._last_data["api_ai_advisor"] = f"☁️ Thời tiết khắc nghiệt. Đang gọi AI..." if vi else "☁️ Extreme weather. Asking AI..."
            elif mode == "anomaly":
                core._last_data["api_ai_advisor"] = f"⚠️ Sụt pin nhanh! Đang chờ AI phân tích..." if vi else "⚠️ Fast battery drop! Analyzing..."
            else:
                core._last_data["api_ai_advisor"] = "🔄 Đang gửi dữ liệu cho AI..." if vi else "🔄 Sending trip data to AI..."
                
            core.trigger_callbacks()
            session = async_get_clientsession(core.hass)
            result = await async_get_ai_advice(session, core.gemini_api_key, ai_model, mode, data_payload, context_data)
            
            core._last_data["api_ai_advisor"] = result
            await core.hass.async_add_executor_job(core._save_state)
            core.trigger_callbacks()
        except Exception:
            _LOGGER.exception("VinFast: lỗi parse GPS/route MQTT")

    def _filter_critical_data(self, key, current_val, fallback_val):
        if current_val is None or str(current_val).strip().upper() in ["NONE", "NULL", "UNKNOWN", ""]:
            return fallback_val
        no_zero_keys = (
            "34183_00001_00009", "34180_00001_00011", "34183_00001_00011", "34180_00001_00007", 
            "34193_00001_00012", "34193_00001_00014", "34193_00001_00019", "34220_00001_00001", 
            "34183_00001_00005", "00006_00001_00000", "00006_00001_00001"  
        )
        odo_keys = ("34183_00001_00003", "34199_00000_00000")
        if key in no_zero_keys or key in odo_keys:
            try:
                c_val_float = float(current_val)
                f_val_float = float(fallback_val) if fallback_val is not None else 0.0
                if key in no_zero_keys and c_val_float <= 0.0001 and f_val_float > 0:
                    return fallback_val
                if key in odo_keys and c_val_float < f_val_float:
                    return fallback_val
            except (ValueError, TypeError):
                pass
        return current_val


    def _on_message(self, client, userdata, msg):
        core = self.core
        current_time = time.time()
        self._provider_retry_delay = 300
        self._next_provider_probe = current_time + 300
        core._last_mqtt_msg_time = current_time 
        
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            data_dict = {}
            items = []
            if isinstance(payload, list): items = payload
            elif isinstance(payload, dict):
                if "data" in payload and isinstance(payload["data"], list): items = payload["data"]
                elif "content" in payload and isinstance(payload["content"], list): items = payload["content"]
            
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            
            for item in items:
                if not isinstance(item, dict): continue
                obj, inst, res = str(item.get("objectId", "0")).zfill(5), str(item.get("instanceId", "0")).zfill(5), str(item.get("resourceId", "0")).zfill(5)
                key = item.get("deviceKey") if "deviceKey" in item else f"{obj}_{inst}_{res}"
                val = item.get("value")

                # [2.9.52] Ghi nhận lastUpdateTime của MQTT để cổng so sánh trong
                # `api_auth._merge_telemetry_response()` biết key nào đang TƯƠI NHẤT.
                # Thiếu bước này, giá trị ping cũ (tốc độ cũ 33–108 s) có thể ghi đè
                # giá trị MQTT mới (cũ 2,08 s) vì cổng chỉ nhìn thấy lut của ping.
                if key:
                    _lut = item.get("lastUpdateTime")
                    if _lut is not None:
                        try:
                            _lut_i = int(_lut)
                        except (TypeError, ValueError):
                            _lut_i = 0
                        if _lut_i:
                            _lm = getattr(core, "_telemetry_lut", None)
                            if not isinstance(_lm, dict):
                                _lm = {}
                                core._telemetry_lut = _lm
                            if _lut_i > _lm.get(key, 0):
                                _lm[key] = _lut_i
                
                if key and val is not None:
                    str_val = str(val).strip()
                    old_val = str(core._last_data.get(key, "N/A"))
                    if old_val != str_val:
                        core._raw_json_dict[key] = str_val
                        core._changelog_buffer.insert(0, {"time": time_str, "code": key, "old_value": old_val, "new_value": str_val})
                
                if key == "56789_00001_00007":
                    if str(val) == "CONNECTION_LOST": core._vehicle_offline = True
                    elif str(val) == "NONE": core._vehicle_offline = False
                
                if key == "34180_00001_00011" and isinstance(val, str) and "profile_email" in val: continue 
                if key and val is not None: data_dict[key] = self._filter_critical_data(key, val, core._last_data.get(key))
            
            if not data_dict: return
            
            t1, t2, t3 = data_dict.get("34193_00001_00012"), data_dict.get("34193_00001_00014"), data_dict.get("34193_00001_00019")
            target_val = t1 if t1 is not None else (t2 if t2 is not None else t3)
            if target_val is not None:
                try:
                    if float(target_val) > 0: core._last_data["api_target_charge_limit"] = float(target_val)
                except (TypeError, ValueError):
                    _LOGGER.debug("VinFast: target charge limit không hợp lệ: %r", target_val)

            core._last_data.update(data_dict)
            core._last_data["api_debug_raw"] = f"Nhận: {len(data_dict)} mã ({time_str})"
            
            # Ghi file debug ra www/ (theo yêu cầu checkpoint)
            import os
            try:
                ha_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                www_dir = os.path.join(ha_config_dir, "www")
                if os.path.isdir(www_dir):
                    debug_file = os.path.join(www_dir, "vinfast_debug_raw.json")
                    raw_snapshot = dict(core._raw_json_dict)
                    def _write_debug():
                        with open(debug_file, "w", encoding="utf-8") as f: json.dump(raw_snapshot, f, ensure_ascii=False)
                    if hasattr(core, "hass") and core.hass and getattr(core.hass, "loop", None):
                        # Schedule ghi file về HA event loop từ MQTT thread
                        import asyncio
                        async def _async_write():
                            await core.hass.async_add_executor_job(_write_debug)
                        asyncio.run_coroutine_threadsafe(_async_write(), core.hass.loop)
                    else:
                        _write_debug()
            except Exception as e:
                _LOGGER.debug(f"VinFast: Lỗi ghi file debug raw - {e}")
            
            for k in ["34180_00001_00010", "34183_00001_00010", "34181_00001_00007"]:
                if k in data_dict and isinstance(data_dict[k], str): core._update_vehicle_name(data_dict[k])
                
        except Exception as e:
            _LOGGER.error(f"VinFast: [MQTT-PARSE] Lỗi parse MQTT message: {e}")
            return

        current_soc = safe_float(core._last_data.get("34183_00001_00009", core._last_data.get("34180_00001_00011", 0)))
        
        try:
            model = getattr(core, "vehicle_model_display", "Unknown").upper()
            if "VF8" in model or "VF9" in model:
                gear = str(core._last_data.get("34187_00000_00000", "1"))
                speed = safe_float(core._last_data.get("34188_00000_00000", 0))
            else: 
                gear = str(core._last_data.get("34183_00001_00001", "1"))
                speed = safe_float(core._last_data.get("34183_00001_00002", 0))

            if speed > 0 or gear in ["2", "4", "D", "R"]:
                core._is_moving = True
                core._last_actual_move_time = current_time
            else:
                core._is_moving = False

            core._is_parked = gear == "1" and not core._is_moving
            if core._is_parked:
                if getattr(core, '_parked_since', None) is None:
                    core._parked_since = current_time
            else:
                core._parked_since = None

            # DEBUG: Log khi gear/speed thay đổi (giử 1 lần/ 10s)
            if not getattr(self, '_last_speed_log', None) or (current_time - self._last_speed_log) > 10:
                self._last_speed_log = current_time
                # [2.9.51] Hạ mức log: đây là log CHẨN ĐOÁN, trước đây để WARNING
                # -> chiếm 661/1077 dòng log (61%) chỉ sau 3 giờ. Muốn đo lại nhịp
                # telemetry thì bật: logger: custom_components.vinfast: debug
                _LOGGER.debug(f"VinFast: [SPEED-DEBUG] model={model} gear={gear} speed={speed} is_moving={core._is_moving} trip_active={getattr(core, '_is_trip_active', False)}")

            vi = core.lang == "vi"
            base_status = ("Đang di chuyển" if vi else "Moving") if core._is_moving else (("Đang đỗ" if vi else "Parked") if gear == "1" else ("Đang dừng" if vi else "Stopped"))

            if core._is_moving and not getattr(core, '_is_trip_active', False):
                core._trip_start_time = current_time
                core._trip_start_soc = current_soc
                core._is_trip_active = True
                core._last_data["api_trip_distance"] = 0.0
                core._last_data["api_trip_efficiency"] = 0.0
                core._trip_accumulated_distance_m = 0.0 
                core._route_coords = [] 
                last_lat = core._last_data.get("api_last_lat")
                last_lon = core._last_data.get("api_last_lon")
                if last_lat is not None and last_lon is not None:
                    core._route_coords.append([round(float(last_lat), 6), round(float(last_lon), 6), 0, int(current_time * 1000)])
                # [2.9.54] WARNING -> INFO: sự kiện vòng đời bình thường.
                _LOGGER.info(
                    f"VinFast: [TRIP-START] Bắt đầu chuyến đi mới! "
                    f"SOC={current_soc:.1f}% gear={gear} speed={speed:.1f}"
                )
                # [2.9.51] FIX thread-safety: code cũ gọi async_add_executor_job từ thread
                # paho-mqtt -> RuntimeError "no running event loop", state không được lưu.
                # asyncio.run_coroutine_threadsafe(
                #     core.hass.async_add_executor_job(core._save_state),
                #     core.hass.loop
                # )
                _schedule_save_state(core)
        except Exception as e:
            _LOGGER.error(f"VinFast: [TRIP-MOVE-DETECT] Lỗi phát hiện di chuyển: {e}")

        try:
            gps_fix = collect_gps_pair(self._pending_gps, data_dict, current_time)
            lat, lon = gps_fix if gps_fix else (0.0, 0.0)

            valid_gps = (
                -90.0 <= lat <= 90.0
                and -180.0 <= lon <= 180.0
                and (lat != 0.0 or lon != 0.0)
            )
            if gps_fix and valid_gps:
                actual_speed_kmh = float(speed)
                timestamp_ms = int(current_time * 1000)

                # Raw keeps paired GPS for diagnostics; route uses only plausible fixes.
                trip_id = int(getattr(core, '_trip_start_time', current_time)) if getattr(core, '_is_trip_active', False) else 0
                if core.trip_store:
                    asyncio.run_coroutine_threadsafe(
                        core.trip_store.async_append_point(
                            core.hass, lat, lon, actual_speed_kmh, 0.0,
                            timestamp_ms, trip_id,
                            getattr(core, '_is_trip_active', False),
                            datetime.datetime.fromtimestamp(current_time).strftime("%Y%m%d"),
                            "mqtt",
                        ),
                        core.hass.loop,
                    )

                last_lat = core._last_data.get("api_last_lat")
                last_lon = core._last_data.get("api_last_lon")
                has_last_fix = last_lat is not None and last_lon is not None
                distance_m = gps_distance_m(float(last_lat), float(last_lon), lat, lon) if has_last_fix else 0.0
                time_diff = max(current_time - getattr(core, '_last_gps_time', current_time), 0.001)
                accepted_fix = distance_m / time_diff * 3.6 <= 180.0 and not (actual_speed_kmh == 0 and distance_m > 30.0)

                if accepted_fix:
                    core._last_lat_lon = f"{lat},{lon}"
                    core._last_data["api_last_lat"] = lat
                    core._last_data["api_last_lon"] = lon
                    core._last_gps_time = current_time
                    if not has_last_fix or distance_m >= 5.0 or time_diff >= 60.0:
                        asyncio.run_coroutine_threadsafe(self._update_location_async(lat, lon), core.hass.loop)

                    if getattr(core, '_is_trip_active', False):
                        point = [round(lat, 6), round(lon, 6), int(actual_speed_kmh), timestamp_ms]
                        if core._route_coords:
                            route_distance_m = gps_distance_m(core._route_coords[-1][0], core._route_coords[-1][1], lat, lon)
                            if route_distance_m >= 1.0:
                                core._trip_accumulated_distance_m += route_distance_m
                                core._eff_gps_dist = getattr(core, '_eff_gps_dist', 0.0) + route_distance_m
                                core._route_coords.append(point)
                        else:
                            core._route_coords.append(point)
                        core._last_data["api_trip_route"] = json.dumps(core._route_coords)
                        _LOGGER.debug("VinFast: [TRIP-GPS] append paired route_pts=%s", len(core._route_coords))
                else:
                    # [2.9.54] WARNING -> DEBUG: lọc nhiễu GPS là việc bình thường, lặp nhiều lần.
                    _LOGGER.debug("VinFast: [TRIP-GPS] Bỏ fix nhảy %.0fm/%.1fs", distance_m, time_diff)

            if getattr(core, '_is_trip_active', False):
                final_trip_dist = core._trip_accumulated_distance_m / 1000.0
                core._last_data["api_trip_distance"] = round(final_trip_dist, 2)

                if final_trip_dist > 0:
                    trip_hrs = (current_time - getattr(core, '_trip_start_time', current_time)) / 3600.0
                    if trip_hrs > 0: core._last_data["api_trip_avg_speed"] = round(final_trip_dist / trip_hrs, 1)

                    if getattr(core, '_trip_start_soc', 0) > current_soc:
                        cap = safe_float(core._last_data.get("api_static_capacity", 0))
                        if cap > 0:
                            energy_used = ((core._trip_start_soc - current_soc) / 100.0) * cap
                            core._last_data["api_trip_energy_used"] = round(energy_used, 2)
                            trip_eff = (energy_used / final_trip_dist) * 100
                            core._last_data["api_trip_efficiency"] = round(trip_eff, 2)
                            
                            # Lưu history để tính Adaptive Range
                            if trip_eff >= 10.0 and trip_eff <= 40.0:
                                if getattr(core, '_trip_efficiency_history', None) is None: core._trip_efficiency_history = []
                                rpp_trip = final_trip_dist / energy_used
                                if len(core._trip_efficiency_history) == 0 or abs(core._trip_efficiency_history[-1] - rpp_trip) > 0.05:
                                    core._trip_efficiency_history.append(rpp_trip)
                                    if len(core._trip_efficiency_history) > 3: core._trip_efficiency_history.pop(0)
                            
                            cost_per_kwh = safe_float(core.options.get("cost_per_kwh", 4000))
                            core._last_data["api_trip_charge_cost"] = round(energy_used * cost_per_kwh)

                    gas_km_per_liter = getattr(core, 'gas_km_per_liter', 15.0)
                    gas_price = safe_float(core.options.get("gas_price", 20000))
                    if gas_km_per_liter > 0:
                        core._last_data["api_trip_gas_cost"] = round((final_trip_dist / gas_km_per_liter) * gas_price)
                        
            # Tính toán "Since Last Charge" (Tiêu thụ kể từ lúc sạc xong)
            if getattr(core, '_since_charge_start_odo', None) and getattr(core, '_since_charge_start_soc', None):
                current_odo = safe_float(core._last_data.get("34183_00001_00003", core._last_data.get("34199_00000_00000", 0)))
                if current_odo > core._since_charge_start_odo:
                    since_charge_dist = current_odo - core._since_charge_start_odo
                    core._last_data["api_since_charge_distance"] = round(since_charge_dist, 1)
                    
                    if core._since_charge_start_soc > current_soc:
                        cap = safe_float(core._last_data.get("api_static_capacity", 0))
                        if cap > 0:
                            since_charge_energy = ((core._since_charge_start_soc - current_soc) / 100.0) * cap
                            core._last_data["api_since_charge_energy_used"] = round(since_charge_energy, 2)
                            if since_charge_dist > 0:
                                core._last_data["api_since_charge_efficiency"] = round((since_charge_energy / since_charge_dist) * 100, 2)

        except Exception:
            _LOGGER.exception("VinFast: lỗi cập nhật security warning")

        if current_soc > 0:
            if getattr(core, '_eff_initial_soc', None) is None or current_soc > core._eff_initial_soc:
                core._eff_initial_soc = current_soc
                core._eff_start_soc = current_soc
                core._eff_gps_dist = 0.0
                core._eff_ignored_first = False
                
            if current_soc < getattr(core, '_eff_start_soc', current_soc):
                if not getattr(core, '_eff_ignored_first', False):
                    if core._eff_initial_soc - current_soc >= 1.0:
                        core._eff_ignored_first = True
                        core._eff_start_soc = current_soc
                        core._eff_gps_dist = 0.0 
                else:
                    drop = core._eff_start_soc - current_soc
                    if drop >= 1.0:
                        dist_km = getattr(core, '_eff_gps_dist', 0.0) / 1000.0
                        if dist_km > 0:
                            eff = dist_km / drop
                            core._last_data["api_calc_range_per_percent"] = round(eff, 2)
                            
                            std_range = safe_float(core._last_data.get("api_static_range", 210))
                            expected_km_per_1 = std_range / 100.0 if std_range > 0 else 2.1
                            
                            if eff < (expected_km_per_1 * 0.70):
                                now = time.time()
                                if now - getattr(core, '_last_ai_anomaly_time', 0) > 7200:
                                    core._last_ai_anomaly_time = now
                                    actual_spd = float(speed)
                                    asyncio.run_coroutine_threadsafe(
                                        self._run_ai_advisor_wrapper("anomaly", {"dist": dist_km, "drop": drop, "expected": expected_km_per_1, "speed": actual_spd}),
                                        core.hass.loop
                                    )
                        
                        core._eff_start_soc = current_soc
                        core._eff_gps_dist = 0.0

        try:
            if "VF8" in model or "VF9" in model: c_status = str(core._last_data.get("34183_00000_00001", "0"))
            else: c_status = str(core._last_data.get("34193_00001_00005", "0"))

            is_charging = (c_status == "1")
            is_fully_charged = False 

            if c_status in ["0", "2", "3", "4"] or getattr(core, '_is_moving', False):
                is_charging = False
                is_fully_charged = False

            t_limit = safe_float(core._last_data.get("api_target_charge_limit", 100))
            if t_limit > 0 and current_soc >= t_limit and (is_charging or c_status in ["2", "3"]):
                is_fully_charged = True
                is_charging = False

            core._is_charging = is_charging
            vi = core.lang == "vi"

            if is_charging: core._last_data["api_vehicle_status"] = "Đang sạc" if vi else "Charging"
            elif is_fully_charged: core._last_data["api_vehicle_status"] = "Đã sạc xong" if vi else "Fully Charged"
            else: core._last_data["api_vehicle_status"] = base_status

            if getattr(core, '_is_first_mqtt_message', True):
                core._is_first_mqtt_message = False
                if not is_charging:
                    core._last_is_charging = False

        except Exception:
            _LOGGER.exception("VinFast: lỗi cập nhật trạng thái sạc MQTT")

        try:
            if core._is_charging and not getattr(core, '_last_is_charging', False):
                core._current_charge_max_power = 0.0
                if current_soc > 0:
                    core._last_data["api_last_charge_start_soc"] = current_soc
                    core._last_data["api_last_charge_end_soc"] = current_soc 
                    core._charge_start_soc = current_soc
                else:
                    core._charge_start_soc = safe_float(core._last_data.get("api_last_charge_start_soc", 0))

                core._charge_calc_soc = core._charge_start_soc
                core._charge_start_time = current_time
                core._charge_calc_time = current_time
                core._last_data["api_live_charge_power"] = 0.0
                core._last_is_charging = True
                
                core._eff_initial_soc = current_soc
                core._eff_start_soc = current_soc
                core._eff_gps_dist = 0.0
                core._eff_ignored_first = False
                
                # [2.9.51] FIX thread-safety (bắt đầu phiên sạc) - xem _schedule_save_state()
                # asyncio.run_coroutine_threadsafe(
                #     core.hass.async_add_executor_job(core._save_state),
                #     core.hass.loop
                # )
                _schedule_save_state(core)
                
            elif core._is_charging and getattr(core, '_last_is_charging', False):
                if current_soc > 0 and current_soc >= core._charge_start_soc:
                    core._last_data["api_last_charge_end_soc"] = current_soc

                if getattr(core, '_charge_calc_soc', 0.0) == 0.0 or current_soc < core._charge_calc_soc:
                    core._charge_calc_soc = current_soc
                    core._charge_calc_time = current_time
                    core._last_data["api_live_charge_power"] = 0.0
                elif current_soc > core._charge_calc_soc and current_soc > 0:
                    delta_soc = current_soc - core._charge_calc_soc
                    delta_time_hrs = (current_time - core._charge_calc_time) / 3600.0
                    cap = safe_float(core._last_data.get("api_static_capacity", 18.64))
                    if cap == 0: cap = 18.64
                    
                    if delta_time_hrs > 0.002: 
                        power = (delta_soc / 100.0) * cap / delta_time_hrs
                        if 0 < power < 360: 
                            if current_time - getattr(core, '_last_api_power_time', 0) > 120:
                                if getattr(core, '_live_charge_power_history', None) is None: core._live_charge_power_history = []
                                core._live_charge_power_history.append(power)
                                if len(core._live_charge_power_history) > 3: core._live_charge_power_history.pop(0)
                                smooth_power = sum(core._live_charge_power_history) / len(core._live_charge_power_history)
                                core._last_data["api_live_charge_power"] = round(smooth_power, 1)
                                
                            core._current_charge_max_power = max(getattr(core, '_current_charge_max_power', 0.0), power)
                            core._last_data["34183_00000_00012"] = round(power, 1)

                    core._charge_calc_soc = current_soc
                    core._charge_calc_time = current_time
                    
                    # Dự đoán thời gian sạc còn lại
                    target_soc = safe_float(core._last_data.get("api_target_charge_limit", 100))
                    live_power = safe_float(core._last_data.get("api_live_charge_power", 0))
                    if target_soc > current_soc and live_power > 0:
                        remain_kwh = ((target_soc - current_soc) / 100.0) * cap
                        est_hrs = remain_kwh / (live_power * 0.90) # Sạc tổng hợp AC/DC hiệu suất ~90%
                        est_mins = int(est_hrs * 60)
                        
                        old_mins = safe_float(core._last_data.get("api_est_charge_remaining_duration", 0))
                        if old_mins == 0 or abs(old_mins - est_mins) >= 2:
                            core._last_data["api_est_charge_remaining_duration"] = est_mins
                            core._last_data["api_est_charge_completion_time"] = datetime.datetime.fromtimestamp(current_time + (est_mins * 60)).isoformat()

                    # [2.9.51] FIX thread-safety (đang sạc, SOC tăng) - xem _schedule_save_state()
                    # asyncio.run_coroutine_threadsafe(
                    #     core.hass.async_add_executor_job(core._save_state),
                    #     core.hass.loop
                    # )
                    _schedule_save_state(core)
                elif current_time - getattr(core, '_charge_calc_time', current_time) > 900:
                    core._last_data["api_live_charge_power"] = 0.0
                    core._last_data["34183_00000_00012"] = 0.0
                    
            elif not core._is_charging and getattr(core, '_last_is_charging', False):
                if current_soc > 0 and current_soc >= getattr(core, '_charge_start_soc', 0):
                    core._last_data["api_last_charge_end_soc"] = current_soc
                else:
                    current_soc = safe_float(core._last_data.get("api_last_charge_end_soc", getattr(core, '_charge_start_soc', 0)))
                    
                delta_soc = current_soc - getattr(core, '_charge_start_soc', 0)
                if getattr(core, '_charge_start_time', 0) > 0:
                    core._last_data["api_last_charge_duration"] = round((current_time - core._charge_start_time) / 60.0, 0)
                
                if delta_soc >= 0.5: 
                    cap = safe_float(core._last_data.get("api_static_capacity", 18.64))
                    if cap == 0: cap = 18.64
                    added_kwh = (delta_soc / 100.0) * cap
                    
                    core._last_data["api_last_charge_energy"] = round(added_kwh / 0.92, 2)
                    core._last_data["api_last_charge_efficiency"] = 92.0
                    
                    is_home_charge = False
                    max_pwr = getattr(core, '_current_charge_max_power', 0.0)
                    try:
                        stations = json.loads(core._last_data.get("api_nearby_stations", "[]"))
                        if not stations or float(stations[0].get("dist", 999)) > 0.5: is_home_charge = True 
                    except (TypeError, ValueError, json.JSONDecodeError):
                        _LOGGER.debug("VinFast: nearby station payload không hợp lệ", exc_info=True)
                    
                    if max_pwr > 0 and max_pwr <= 11.0: is_home_charge = True 
                        
                    async def verify_and_update_charge():
                        await asyncio.sleep(15)
                        prev_pub = int(core._last_data.get("api_public_charge_sessions", 0))
                        prev_history = core._last_data.get("api_charge_history_list", "[]")
                        max_attempts = 6 if max_pwr > 5.0 else 2
                        api_success = False
                        
                        for attempt in range(max_attempts):
                            if attempt > 0: await asyncio.sleep(30)
                            await core.auth.fetch_charging_history()
                            new_pub = int(core._last_data.get("api_public_charge_sessions", 0))
                            new_history = core._last_data.get("api_charge_history_list", "[]")
                            
                            if new_pub > prev_pub:
                                api_success = True
                                try:
                                    history_list = json.loads(new_history)
                                    if history_list and len(history_list) > 0:
                                        rest_kwh = float(history_list[0].get("kwh", 0.0))
                                        if rest_kwh > 0.0:
                                            eff = (added_kwh / rest_kwh) * 100.0
                                            core._last_data["api_last_charge_energy"] = round(rest_kwh, 2)
                                            core._last_data["api_last_charge_efficiency"] = round(min(eff, 100.0), 1)
                                except Exception:
                                    _LOGGER.debug("VinFast: không thể tính hiệu suất phiên sạc", exc_info=True)
                                break
                            if new_history == prev_history and prev_history != "[]" and is_home_charge and max_pwr <= 11.0:
                                break

                        if not api_success:
                            core._last_data["api_home_charge_sessions"] = int(core._last_data.get("api_home_charge_sessions", 0)) + 1
                            core._last_data["api_home_charge_kwh"] = round(float(core._last_data.get("api_home_charge_kwh", 0.0)) + added_kwh, 2)
                        
                        await core.hass.async_add_executor_job(core._save_state)
                        core.trigger_callbacks()

                    asyncio.run_coroutine_threadsafe(
                        verify_and_update_charge(),
                        core.hass.loop
                    )
                
                core._last_is_charging = False
                core._charge_calc_soc = 0.0
                core._charge_calc_time = current_time
                core._last_data["api_live_charge_power"] = 0.0
                core._last_data["34183_00000_00012"] = 0.0
                core._current_charge_max_power = 0.0 
                core._live_charge_power_history = []
                core._last_data["api_est_charge_remaining_duration"] = 0
                if "api_est_charge_completion_time" in core._last_data:
                    del core._last_data["api_est_charge_completion_time"]
                
                if delta_soc >= 2.0:
                    current_odo = safe_float(core._last_data.get("34183_00001_00003", core._last_data.get("34199_00000_00000", 0)))
                    if current_odo > 0:
                        core._since_charge_start_odo = current_odo
                        core._since_charge_start_soc = current_soc
                        core._last_data["api_since_charge_distance"] = 0.0
                        core._last_data["api_since_charge_energy_used"] = 0.0
                        core._last_data["api_since_charge_efficiency"] = 0.0

                # [2.9.51] FIX thread-safety (kết thúc phiên sạc) - xem _schedule_save_state()
                # asyncio.run_coroutine_threadsafe(
                #     core.hass.async_add_executor_job(core._save_state),
                #     core.hass.loop
                # )
                _schedule_save_state(core)

        except Exception:
            _LOGGER.exception(
                "VinFast: lỗi kết thúc phiên sạc MQTT "
                "(is_charging=%s, last_is_charging=%s)",
                getattr(core, '_is_charging', None),
                getattr(core, '_last_is_charging', None),
            )

        try:
            open_doors = []
            
            door_map = {
                "10351_00002_00050": "Cửa lái", "10351_00001_00050": "Cửa phụ",
                "10351_00004_00050": "Cửa sau T", "10351_00003_00050": "Cửa sau P",
                "10351_00006_00050": "Cốp", "10351_00005_00050": "Capo"
            }
            for dk, dname in door_map.items():
                if str(core._last_data.get(dk, "0")) == "1": open_doors.append(dname)
                
            window_map = {
                "34215_00002_00002": "Kính lái", "34215_00001_00002": "Kính phụ",
                "34215_00004_00002": "Kính sau T", "34215_00003_00002": "Kính sau P"
            }
            for wk, wname in window_map.items():
                if str(core._last_data.get(wk, "0")) == "2": open_doors.append(wname)
            
            model_name = getattr(core, "vehicle_model_display", "Unknown").upper()
            
            lock_1 = str(core._last_data.get("34213_00001_00003", "1"))
            is_unlocked = (lock_1 == "0")
            
            if "VF5" in model_name or "VF 5" in model_name or "VF6" in model_name or "VF 6" in model_name or "VF7" in model_name or "VF 7" in model_name or "E34" in model_name:
                lock_2 = str(core._last_data.get("34206_00001_00001", "1"))
                if lock_2 == "0":
                    is_unlocked = True
                    
            is_parked = (gear == "1") 
            
            # Khi xe đang khóa tổng, mọi trạng thái cửa cũ chưa kịp hạ được coi là đã đóng kín
            if not is_unlocked:
                for dk in ["10351_00002_00050", "10351_00001_00050", "10351_00004_00050", "10351_00003_00050", "10351_00006_00050", "10351_00005_00050"]:
                    if dk in core._last_data and str(core._last_data[dk]) == "1":
                        core._last_data[dk] = "0"
                open_doors = [d for d in open_doors if d not in ["Cửa lái", "Cửa phụ", "Cửa sau T", "Cửa sau P", "Cốp", "Capo"]]

            warnings = []
            if open_doors: 
                warnings.append(f"Đang mở {', '.join(open_doors)}")
            if is_parked and is_unlocked: 
                warnings.append("Chưa khóa xe")
            
            if warnings:
                core._last_data["api_security_warning"] = " | ".join(warnings)
            else:
                core._last_data["api_security_warning"] = "An toàn"
        except Exception: 
            pass

        core.trigger_callbacks()
