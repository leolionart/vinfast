import time
import datetime
import hashlib
import hmac
import base64
import urllib.parse
import asyncio
import logging
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEVICE_ID
try:
    from .const import CONF_UAA_CLIENT_INSTANCE_ID, CONF_UAA_SIGNATURE, CONF_UAA_TIMESTAMP
except ImportError:
    CONF_UAA_CLIENT_INSTANCE_ID = "uaa_client_instance_id"
    CONF_UAA_SIGNATURE = "uaa_signature"
    CONF_UAA_TIMESTAMP = "uaa_timestamp"
from .model_registry import get_vehicle_profile
from .api_helpers import distance_total_unchanged, safe_float

_LOGGER = logging.getLogger(__name__)

KNOWN_IOT_PROVIDERS = ("AWS", "EMQX")


def normalize_iot_provider(value):
    provider = str(value or "").strip().upper()
    return provider if provider in KNOWN_IOT_PROVIDERS else None


class AuthManager:
    def __init__(self, core):
        self.core = core
        self._login_lock = asyncio.Lock()
        self._last_login_time = 0

    def _device_id(self):
        """X-Device-Identifier dùng cho mọi request.

        Thứ tự ưu tiên: tuỳ chọn ``device_id`` của config entry → bảng
        ``DEVICE_ID_BY_EMAIL`` trong ``const.py`` → ``DEVICE_ID``.

        Quyền gọi ``telemetry/app/ping`` gắn với CẶP (tài khoản, device id), nên hai
        xe khác tài khoản cần hai device id khác nhau. Phần ``const.py`` được bọc
        trong try/except để bản const.py CŨ (chưa có ``device_id_for``) vẫn chạy.
        """
        options = getattr(self.core, "options", None) or {}
        data = getattr(self.core, "data", None) or {}
        for src in (options, data):
            value = str(src.get("device_id") or "").strip()
            if value:
                return value
        try:
            from .const import device_id_for
            return device_id_for(getattr(self.core, "email", "")) or DEVICE_ID
        except Exception:
            return DEVICE_ID

    def _sign_waf(self, payload_str, method, uri, ts):
        if not getattr(self.core, 'private_key', None):
            return ""
        payload_to_sign = f"{ts}{method.upper()}{uri}{payload_str}"
        sig_bytes = self.core.private_key.sign(
            payload_to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(sig_bytes).decode('utf-8')

    def _xhash2_payload(self, method, uri, ts):
        normalized = uri.split('?', 1)[0].lstrip('/').replace('/', '_')
        parts = ['android']
        if getattr(self.core, 'vin', None) and self.core.vin != 'none':
            parts.append(str(self.core.vin).strip())
        parts.extend([str(getattr(self.core, 'device_id', '') or '').strip(), normalized, method.upper(), str(ts)])
        return '_'.join(parts).lower()

    async def api_request(self, method, uri, body_dict=None, params=None, max_retries=1, custom_vin=None, reauth_on_403=True):
        session = async_get_clientsession(self.core.hass)
        
        for attempt in range(max_retries + 1):
            ts = str(int(time.time() * 1000))
            
            # Phải giữ nguyên cấu trúc {} nếu có
            if body_dict is not None:
                payload_str = json.dumps(body_dict, separators=(',', ':'))
            else:
                payload_str = ""
            # Xử lý URI chứa query string cho WAF signature
            from urllib.parse import urlencode
            sign_uri = uri
            if params:
                query_string = urlencode(params)
                sign_uri = f"{uri}?{query_string}"
            
            x_hash = self._sign_waf(payload_str, method.upper(), sign_uri, ts)
            active_token = getattr(self.core, 'vf_token', None) or getattr(self.core, 'access_token', None) or ""
            device_id = self._device_id()

            headers = {
                "Authorization": f"Bearer {active_token}",
                "X-Device-Identifier": device_id,
                "X-APP-VERSION": "2.22.18",
                "X-Device-Family": "SM-F916N",
                "X-Device-Locale": "vi_VN",
                "X-Device-Platform": "android",
                "X-Device-OS-Version": "android 13",
                "X-SERVICE-NAME": "CAPP",
                "X-Timezone": "Asia/Ho_Chi_Minh",
                "X-TIMESTAMP": ts,
                "X-HASH": x_hash,
                "User-Agent": f"android - {device_id} - 2.22.18",
                "Content-Type": "application/json; charset=UTF-8"
            }
            
            if self.core.email: 
                headers["X-Player-Identifier"] = self.core.email
                
            req_vin = custom_vin or self.core.vin
            # [2.9.54] Hạ WARNING -> DEBUG. Đây là TRACE chẩn đoán, không phải cảnh báo:
            # đo trên log thật, dòng [COMPONENT-API] chiếm 30/89 dòng (34%) toàn bộ log,
            # 2,8 lời gọi/phút => ~4.000 dòng/ngày. Muốn xem lại thì:
            #   logger: logs: { custom_components.vinfast.api_auth: debug }
            _LOGGER.debug(f"VinFast: [COMPONENT-API] {method.upper()} {uri} payload={payload_str[:300]} headers={{k: headers[k] for k in ['X-APP-VERSION','X-Device-Family','X-Device-Platform','X-DEVICE-OS-VERSION','X-HASH'] if k in headers}}")
            if req_vin and req_vin != "none": headers["X-VIN-CODE"] = req_vin

            url = f"{self.core.api_base}{uri}"
            
            # aiohttp.web_response class wraps response status
            try:
                # Custom mock class to mimic requests Response for backward compatibility
                class AsyncResponse:
                    def __init__(self, status_code, text, json_data):
                        self.status_code = status_code
                        self.text = text
                        self._json = json_data
                    def json(self):
                        return self._json
                
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=payload_str.encode('utf-8') if payload_str else None,
                    timeout=15
                ) as res:
                    status = res.status
                    text = await res.text()
                    try:
                        res_json = await res.json()
                    except Exception:
                        res_json = {}
                        
                    res_wrapped = AsyncResponse(status, text, res_json)
                    
                    if status in [401, 403]:
                        # [2.9.53] 403 KHÔNG đồng nghĩa token hết hạn. Đo trên log thật:
                        # MỌI lần ping bị 403 đều kéo theo một lần đăng nhập lại Auth0 vô ích
                        # (57 lần / 137 phút, ~86 s lãng phí) rồi gọi lại vẫn 403.
                        # [2.9.55] ĐÍNH CHÍNH nguyên nhân: 403 ở `telemetry/app/ping` là do
                        # XE KHÔNG PHẢN HỒI (TCU ngủ), không phải do tài khoản. Cùng một script,
                        # cùng tài khoản, cùng payload: 18:0x/19:10 khi xe ĐANG CHẠY -> 200;
                        # từ 19:25 khi TCU CONNECTION_LOST -> 403. Vì vậy: không đăng nhập lại.
                        if status == 403 and not reauth_on_403:
                            _LOGGER.debug(
                                "VinFast: API %s bị từ chối quyền (403) — không phải token "
                                "hết hạn, không đăng nhập lại", uri)
                            return res_wrapped
                        if time.time() - getattr(self, '_last_login_time', 0) > 30:
                            _LOGGER.warning(f"VinFast: Token hết hạn (Mã {status}), đang xin lại Token mới...")
                            if not await self.login():
                                _LOGGER.error("VinFast: không thể làm mới token sau phản hồi %s", status)
                                return res_wrapped
                            continue
                        else:
                            _LOGGER.debug(f"VinFast: API {uri} từ chối truy cập (Mã {status}). Bỏ qua.")
                            return res_wrapped
                    return res_wrapped
            except (asyncio.TimeoutError, TimeoutError):
                _LOGGER.debug(f"VinFast: API {uri} quá thời gian chờ (>15s), bỏ qua lần thử này.")
                await asyncio.sleep(1)
            except Exception as e:
                err_detail = f"{type(e).__name__}: {e!r}" if not str(e) else str(e)
                _LOGGER.warning(f"VinFast Request Error ({uri}): {err_detail}")
                await asyncio.sleep(2)
        return None

    async def login(self):
        async with self._login_lock:
            # Ngăn chặn việc login song song liên tục
            if time.time() - getattr(self, '_last_login_time', 0) < 30:
                return getattr(self.core, 'vf_token', None)

            _LOGGER.info("VinFast: [AUTH] Đang khởi tạo đăng nhập...")
            if not getattr(self.core, 'private_key', None): self.core._load_private_key()
            if not getattr(self.core, 'private_key', None): return None

            session = async_get_clientsession(self.core.hass)

            # 1. Auth0 Login
            auth0_url = f"{self.core.auth0_domain}/oauth/token"
            if not auth0_url.startswith("http"): auth0_url = f"https://{auth0_url}"
            
            auth0_payload = {
                "grant_type": "password", "client_id": self.core.auth0_client_id, "audience": self.core.api_base,
                "username": str(self.core.email or "").strip(), "password": str(self.core.password or "").strip(),
                "scope": "offline_access openid profile email read:current_user update:current_user_metadata",
                "connection": "Username-Password-Authentication"
            }
            auth0_headers = {
                "X-Device-Identifier": self._device_id(),
                "X-APP-VERSION": "2.21.3",
                "X-TIMESTAMP": str(int(time.time() * 1000)),
                "Content-Type": "application/json; charset=UTF-8"
            }
            
            auth0_headers["X-APP-VERSION"] = "2.22.18"
            auth0_ok = False
            for attempt in range(3):
                try:
                    async with session.post(auth0_url, json=auth0_payload, headers=auth0_headers, timeout=15) as res_auth0:
                        if res_auth0.status == 200:
                            res_json = await res_auth0.json()
                            self.core.access_token = res_json.get("access_token")
                            id_token = res_json.get("id_token")
                            if id_token and not getattr(self.core, 'user_id', None):
                                try:
                                    parts = id_token.split(".")
                                    if len(parts) >= 2:
                                        padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                                        claims = json.loads(base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8'))
                                        if "sub" in claims:
                                            self.core.user_id = claims["sub"]
                                except Exception:
                                    pass
                            _LOGGER.info("VinFast: [AUTH] Bước 1 - Đăng nhập Auth0 thành công!")
                            auth0_ok = True
                            break
                        elif res_auth0.status == 429:
                            _LOGGER.warning("VinFast: [AUTH] Auth0 tạm khóa do quá nhiều lần thử (429). Tạm dừng thử lại để chờ mở khóa.")
                            self._last_login_time = time.time() + 300
                            auth0_ok = False
                            break
                        else:
                            _LOGGER.error(f"VinFast: [AUTH] Auth0 thất bại! Mã: {res_auth0.status} (lần {attempt+1})")
                except Exception as e:
                    _LOGGER.warning(f"VinFast: [AUTH] Lỗi kết nối Auth0 (lần {attempt+1}): {type(e).__name__} {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
            if not auth0_ok:
                return None

            # 2. UAA Token Exchange
            opts = getattr(self.core, 'options', {})
            data = getattr(self.core, 'data', {})
            
            uaa_client_id = opts.get(CONF_UAA_CLIENT_INSTANCE_ID, data.get(CONF_UAA_CLIENT_INSTANCE_ID, ""))
            uaa_signature = opts.get(CONF_UAA_SIGNATURE, data.get(CONF_UAA_SIGNATURE, ""))
            uaa_timestamp = opts.get(CONF_UAA_TIMESTAMP, data.get(CONF_UAA_TIMESTAMP, ""))
            
            # Failsafe fallback: Lấy từ const.py cũ nếu user hardcode
            if not uaa_client_id:
                from . import const
                uaa_client_id = getattr(const, "UAA_CLIENT_INSTANCE_ID", "")
                uaa_signature = getattr(const, "UAA_SIGNATURE", "")
                uaa_timestamp = getattr(const, "UAA_TIMESTAMP", "")

            if not uaa_client_id or not uaa_signature or not uaa_timestamp or str(uaa_client_id).startswith("THAY_BANG"):
                _LOGGER.warning("VinFast [Failsafe]: Thiếu hoặc chưa cấu hình UAA credential. Chạy ở chế độ giới hạn (không điều khiển từ xa).")
                return None
                
            uaa_body = urllib.parse.urlencode({
                "grant_type": "app", "timestamp": str(uaa_timestamp).strip(),
                "clientInstanceId": str(uaa_client_id).strip(), "signature": str(uaa_signature).strip()
            })
            ts_uaa = str(int(time.time() * 1000))
            x_hash = self._sign_waf(uaa_body, "POST", "/ccaruaa/oauth/token", ts_uaa)
            
            uaa_headers = {
                "Authorization": "Basic Y2FwcDhPWFdEOWJGYkdpRkc6YnFGZ2pLQ0I2U0pqZ0w3bQ==",
                "X-Device-Identifier": self._device_id(), "X-APP-VERSION": "2.22.18", "X-Device-Family": "SM-F916N",
                "X-Device-Locale": "vi_VN", "X-Device-Platform": "android", "X-SERVICE-NAME": "CAPP",
                "X-TIMESTAMP": ts_uaa, "X-HASH": x_hash, "Content-Type": "application/x-www-form-urlencoded"
            }
            
            for attempt in range(3):
                try:
                    ts_uaa = str(int(time.time() * 1000))
                    x_hash = self._sign_waf(uaa_body, "POST", "/ccaruaa/oauth/token", ts_uaa)
                    uaa_headers["X-TIMESTAMP"] = ts_uaa
                    uaa_headers["X-HASH"] = x_hash
                    async with session.post(f"{self.core.api_base}/ccaruaa/oauth/token", data=uaa_body, headers=uaa_headers, timeout=15) as res_uaa:
                        if res_uaa.status == 200:
                            res_json = await res_uaa.json()
                            self.core.vf_token = res_json.get("access_token")
                            if not self.core.vf_token:
                                _LOGGER.error("VinFast: UAA trả 200 nhưng không có access_token")
                                return None
                            self._last_login_time = time.time()
                            _LOGGER.info("VinFast: [AUTH] Bước 2 - Quy đổi Token UAA thành công!")
                            return self.core.vf_token
                        else:
                            _LOGGER.error(f"VinFast: [AUTH] UAA thất bại! Mã: {res_uaa.status} (lần {attempt+1})")
                except Exception as e:
                    _LOGGER.warning(f"VinFast: [AUTH] Lỗi kết nối UAA (lần {attempt+1}): {type(e).__name__} {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
            return None

    async def get_vehicles(self):
        _LOGGER.info("VinFast: Đang gọi lấy danh sách xe...")
        res = await self.api_request("GET", "/ccarusermgnt/api/v1/user-vehicle", custom_vin="none")
        if res and res.status_code == 200:
            vehicles = res.json().get("data", [])
            if vehicles:
                # Prefer the configured VIN; multi-vehicle accounts must not use item 0 blindly.
                v = next((item for item in vehicles if item.get("vinCode") == self.core.vin), None) if self.core.vin else None
                if self.core.vin and not v:
                    _LOGGER.error("VinFast: VIN cấu hình không tồn tại trong danh sách xe")
                    return []
                v = v or next((item for item in vehicles if item.get("isSelected")), None) or vehicles[0]
                self.core.user_id = str(v.get("userId", ""))
                raw_provider = v.get("iotProvider")
                self.core.iot_provider = normalize_iot_provider(raw_provider)
                if raw_provider and not self.core.iot_provider:
                    _LOGGER.warning("VinFast: Provider chưa hỗ trợ từ server: %s", raw_provider)
                if not self.core.vin: self.core.vin = v.get("vinCode", "")
                await self.core._load_state()

                self.core.vehicle_model_display = v.get("marketingName") or v.get("dmsVehicleModel") or "VF"
                self.core._last_data["api_vehicle_model"] = self.core.vehicle_model_display
                
                plate = v.get("licensePlate")
                custom_name = v.get("customizedVehicleName")
                if plate and len(str(plate)) > 3 and str(plate).lower() != "vinfast": self.core.vehicle_name = plate
                elif custom_name and len(str(custom_name)) > 1 and not str(custom_name).isnumeric() and str(custom_name).lower() != "vinfast": self.core.vehicle_name = custom_name
                else: self.core.vehicle_name = self.core.vehicle_model_display
                self.core._last_data["api_vehicle_name"] = self.core.vehicle_name
                
                # ponytail: only use S3 vehicle image. Block user avatarUrl/vehicleAvatar to avoid user's avatar showing. Force http.
                img_url = v.get("vehicleImage")
                if img_url and "/content/carimage/" in img_url:
                    img_url = img_url.replace("https://", "http://")
                else:
                    model_display = (v.get("marketingName") or v.get("dmsVehicleModel") or "VF3").upper()
                    if "VF8" in model_display:
                        img_url = "http://public.s3.connected-car.vinfast.vn/content/carimage/CE19_2024_CE19.png"
                    elif "VF9" in model_display:
                        img_url = "http://public.s3.connected-car.vinfast.vn/content/carimage/CE20_2024_CE20.png"
                    else:
                        img_url = "http://public.s3.connected-car.vinfast.vn/content/carimage/EI13_2024_CE18.png"
                if img_url: self.core._last_data["api_vehicle_image"] = img_url
                
                profile = get_vehicle_profile(self.core.vehicle_model_display)
                self.core._active_sensors = profile["sensors"]
                self.core._vehicle_spec = profile["spec"]
                self.core.ev_kwh_per_km = safe_float(self.core.options.get("ev_kwh_per_km", self.core._vehicle_spec.get("ev_kwh_per_km", 0.15)))
                self.core.gas_km_per_liter = safe_float(self.core.options.get("gas_km_per_liter", self.core._vehicle_spec.get("gas_km_per_liter", 15.0)))
                self.core._calculate_advanced_stats()
                
                _LOGGER.info(f"VinFast: Đang nạp Từ điển Cảm biến cho {self.core.vehicle_model_display}...")
                try:
                    res_alias = await self.api_request("GET", "/modelmgmt/api/v2/vehicle-model/mobile-app/vehicle/get-alias?version=0.0.0")
                    if res_alias and res_alias.status_code == 200:
                        alias_data = res_alias.json().get("resources", [])
                        count = 0
                        for r in alias_data:
                            obj_id = str(r.get('devObjID')).zfill(5)
                            inst_id = str(r.get('devObjInstID') or 1).zfill(5)
                            rsrc_id = str(r.get('devRsrcID') or 0).zfill(5)
                            
                            key = f"{obj_id}_{inst_id}_{rsrc_id}"
                            name = r.get("name")
                            
                            if key and name:
                                self.core.dynamic_alias_map[key] = name
                                count += 1
                        _LOGGER.info(f"VinFast: Đã nạp thành công {count} từ vựng từ máy chủ VinFast!")
                except Exception as e:
                    _LOGGER.error(f"VinFast: Lỗi tải Từ điển cảm biến - {e}")

                # Đường dẫn đúng theo APK: /ccarusermgnt/api/v1/auth0/account/profile
                # (bản cũ gọi /ccarusermgnt/api/v1/profile và luôn nhận 404)
                res_profile = await self.api_request("GET", "/ccarusermgnt/api/v1/auth0/account/profile")
                if res_profile and res_profile.status_code == 200:
                    profile = res_profile.json().get("data", {}) or {}
                    profile_id = str(profile.get("id", "") or "")
                    if profile_id:
                        self.core.user_id = profile_id
                    if profile.get("name"):
                        self.core._last_data["api_profile_name"] = profile.get("name")
                    if profile.get("phoneNumber"):
                        self.core._last_data["api_profile_phone"] = profile.get("phoneNumber")
            return vehicles
        return []

    async def get_provider_credentials(self, provider):
        provider = normalize_iot_provider(provider)
        if not provider or not self.core.vin:
            return None
        uri = "/ccarusermgnt/api/v1/auth0/account/client/credentials"
        # POST is the current contract. AWS GET remains a compatibility fallback for older servers.
        res = await self.api_request(
            "POST", uri,
            body_dict={"vinCode": self.core.vin, "iotProvider": provider},
        )
        if (not res or res.status_code in (404, 405)) and provider == "AWS":
            res = await self.api_request("GET", uri)
        if not res or res.status_code != 200:
            _LOGGER.warning("VinFast: Không lấy được credentials provider=%s status=%s", provider, getattr(res, "status_code", None))
            return None
        data = res.json().get("data", {}) or {}
        if provider == "EMQX" and not data.get("sessionToken"):
            _LOGGER.warning("VinFast: Credentials EMQX thiếu sessionToken")
            return None
        if provider == "AWS" and not all(data.get(k) for k in ("accessKeyId", "secretKeyId", "sessionToken")):
            _LOGGER.warning("VinFast: Credentials AWS thiếu STS fields")
            return None
        return data

    async def refresh_iot_provider(self):
        """Read the provider for the configured VIN without reloading vehicle metadata."""
        res = await self.api_request("GET", "/ccarusermgnt/api/v1/user-vehicle", custom_vin="none")
        if not res or res.status_code != 200:
            return None
        vehicles = res.json().get("data", []) or []
        vehicle = next((item for item in vehicles if item.get("vinCode") == self.core.vin), None)
        if not vehicle:
            return None
        raw_provider = vehicle.get("iotProvider")
        provider = normalize_iot_provider(raw_provider)
        if raw_provider and not provider:
            _LOGGER.warning("VinFast: Provider chưa hỗ trợ từ server: %s", raw_provider)
        return provider

    async def get_aws_credentials(self):
        return await self.get_provider_credentials("AWS")

    async def get_emqx_credentials(self):
        return await self.get_provider_credentials("EMQX")

    def register_device_trust(self): pass

    #: [2.9.53] Gặp 403 ở telemetry ping thì chỉ thử lại sau ngần này giây.
    #: [2.9.55] ĐÍNH CHÍNH nguyên nhân: 403 KHÔNG phải "tài khoản thiếu quyền".
    #: Đo trên cùng một script, cùng tài khoản, cùng payload:
    #:    18:0x và 19:10 (xe ĐANG CHẠY)      -> HTTP 200 (6 và 37 key)
    #:    từ 19:25 (TCU CONNECTION_LOST, xe đỗ/ngủ) -> HTTP 403 "Unauthorized"
    #: Với đúng credential của từng tài khoản, CẢ chủ xe lẫn tài xế đều 403 khi xe ngủ.
    #: => 403 ở endpoint này là "XE KHÔNG PHẢN HỒI", không phải chuyện tài khoản.
    TELEMETRY_PING_RETRY_S = 600

    #: [2.9.56] Endpoint đánh thức TCU. Bằng chứng: APK 2.26.11,
    #: ``DrivingAssistApi.d()`` mang ``@POST("ccaraccessmgmt/api/v1/remote/app/wakeup")``
    #: và **không có tham số** (POST rỗng, không body).
    #: Đo thật 2026-10-10 với VF6 đang ngủ: ``HTTP 200 {"code":200000,"message":"Success"}``.
    #: Sau wakeup, TCU cần thời gian thức nên ping vẫn 403 trong lúc chờ.
    WAKEUP_URI = "/ccaraccessmgmt/api/v1/remote/app/wakeup"
    #: Không gọi wakeup dày hơn ngần này (tránh đánh thức xe liên tục khi xe ngủ qua đêm).
    WAKEUP_COOLDOWN_S = 300
    #: Sau wakeup, mở cửa sổ cho phép ping lại nhanh để bắt lúc TCU vừa thức.
    WAKEUP_PING_WINDOW_S = 180

    def _vehicle_is_awake(self, now=None):
        """[2.9.55] Xe có đang thức không? Dựa vào message MQTT gần đây.

        `telemetry/app/ping` chỉ trả dữ liệu khi phiên TCU còn sống; khi xe ngủ thì
        server trả 403. Biết xe đang thức giúp tránh gọi ping vô ích và biết lúc nào
        nên thử lại ngay thay vì chờ hết hạn chặn.
        """
        now = now or time.time()
        if getattr(self.core, "_vehicle_offline", False):
            return False
        last = getattr(self.core, "_last_mqtt_msg_time", 0)
        return bool(last) and (now - last) < 300

    async def register_resources(self, force=False):
        try:
            now = time.time()
            # [2.9.53] CHỐNG VÒNG LẶP 403. Đo trên log thật 137 phút (xe đang chạy):
            #   117 lời gọi ping -> mỗi lần 403 -> api_request hiểu nhầm là "token hết hạn"
            #   -> đăng nhập lại Auth0 -> gọi lại -> 403. Tổng 57 lần đăng nhập lại (~86 s).
            # [2.9.55] Thêm: nếu xe VỪA THỨC trở lại (có message MQTT mới) thì thử lại NGAY,
            # vì lúc đó ping mới có ý nghĩa.
            denied = getattr(self, "_telemetry_ping_denied", False)
            # [2.9.56] Ngay sau wakeup, bỏ qua chặn 403 để ping lại nhanh và bắt lúc TCU vừa thức.
            in_wakeup_window = now < getattr(self, "_wakeup_ping_until", 0)
            if denied and not force and not in_wakeup_window:
                if self._vehicle_is_awake(now):
                    self._telemetry_ping_denied = False      # xe thức -> thử lại
                elif now - getattr(self, "_telemetry_ping_denied_at", 0) \
                        < self.TELEMETRY_PING_RETRY_S:
                    self.core._last_auto_wakeup_time = now
                    return 0

            active_dict = getattr(self.core, '_active_sensors', {})
            # [2.9.56] Ba trường định danh tài nguyên phải là SỐ NGUYÊN, không phải chuỗi:
            # `VehiclePingResourceDto` (classes8.dex, APK 2.26.11) khai báo
            # ``resourceId``/``instanceId``/``objectId`` kiểu ``Integer``.
            # Gửi chuỗi số vẫn được server chấp nhận nhưng sai kiểu so với app.
            reqs = [{"instanceId": int(k.split("_")[1]), "objectId": int(k.split("_")[0]), "resourceId": int(k.split("_")[2])} for k in active_dict.keys() if "_" in k and not k.startswith("api_")]
            if reqs:
                # [2.9.52] FIX: response của ping là nguồn LÀM TƯƠI / DỰ PHÒNG cho nhóm key
                # "theo thay đổi" (vị trí cần số, ODO, SOC, quãng đường). Code cũ vứt bỏ
                # response nên không dùng được dữ liệu đó.
                # [2.9.53] reauth_on_403=False: 403 ở endpoint này KHÔNG phải token hết hạn
                # (xem đính chính ở TELEMETRY_PING_RETRY_S) -> không kích hoạt đăng nhập lại.
                # await self.api_request("POST", "/ccaraccessmgmt/api/v1/telemetry/app/ping", reqs[:50])
                res = await self.api_request(
                    "POST", "/ccaraccessmgmt/api/v1/telemetry/app/ping", reqs[:50],
                    reauth_on_403=False)
                st = getattr(res, "status_code", 0)
                if st == 403:
                    if not getattr(self, "_telemetry_ping_denied", False):
                        # [2.9.57] Ghi rõ tài khoản + device id: 403 phụ thuộc CẶP
                        # (tài khoản, X-Device-Identifier), không phải trạng thái TCU.
                        _LOGGER.warning(
                            "VinFast: [TELEMETRY-PING] HTTP 403 — account=%s device=%s "
                            "(%d resource). Sai X-Device-Identifier cũng cho 403 y hệt "
                            "xe đang ngủ, nên phải kiểm tra device id trước.",
                            self.core.email, DEVICE_ID, len(reqs[:50]))
                    self._telemetry_ping_denied = True
                    self._telemetry_ping_denied_at = now
                    # [2.9.56] Ping 403 = TCU ngủ. Xin đánh thức rồi ping lại trong cửa sổ wakeup.
                    if now - getattr(self, "_last_wakeup_time", 0) >= self.WAKEUP_COOLDOWN_S:
                        try:
                            self.core.hass.async_create_task(self.wake_vehicle())
                        except Exception:
                            _LOGGER.debug("VinFast: không tạo được task wakeup", exc_info=True)
                elif st == 200:
                    if getattr(self, "_telemetry_ping_denied", False):
                        _LOGGER.info(
                            "VinFast: [TELEMETRY-PING] xe đã phản hồi trở lại — bật lại vòng làm tươi.")
                    _LOGGER.info(
                        "VinFast: [TELEMETRY-PING] HTTP 200 — account=%s device=%s",
                        self.core.email, DEVICE_ID)
                    self._telemetry_ping_denied = False
                self._merge_telemetry_response(res)
            self.core._last_auto_wakeup_time = time.time()
        except Exception:
            _LOGGER.exception("VinFast: ping telemetry resources thất bại (có thể do tài khoản phụ không có quyền)")

    async def wake_vehicle(self, force=False):
        """[2.9.56] Đánh thức TCU để xe bắt đầu đẩy toạ độ/telemetry.

        Vì sao cần: khi xe đỗ lâu, TCU ngủ nên (a) MQTT im lặng và (b) ``telemetry/app/ping``
        trả 403, khiến toạ độ không bao giờ về. App VinFast xử lý bằng cách gọi endpoint
        wakeup trước rồi mới đọc telemetry; component phải làm tương tự.

        Body rỗng là ĐÚNG giao thức: ``DrivingAssistApi.d()`` trong APK 2.26.11 không có
        tham số nào. Trả ``True`` khi server nhận lệnh (``code`` 200xxx).
        """
        now = time.time()
        if not force and now - getattr(self, "_last_wakeup_time", 0) < self.WAKEUP_COOLDOWN_S:
            return False
        self._last_wakeup_time = now
        try:
            res = await self.api_request("POST", self.WAKEUP_URI, reauth_on_403=False)
        except Exception:
            _LOGGER.debug("VinFast: gọi wakeup thất bại", exc_info=True)
            return False

        status = getattr(res, "status_code", 0)
        code = None
        try:
            body = res.json() if res is not None else {}
            if isinstance(body, dict):
                code = body.get("code")
        except Exception:
            body = {}

        if status == 200 and (code is None or int(code) // 1000 == 200):
            # Cho phép ping lại ngay trong cửa sổ này để bắt lúc TCU vừa thức.
            self._wakeup_ping_until = now + self.WAKEUP_PING_WINDOW_S
            self._telemetry_ping_denied = False
            _LOGGER.info(
                "VinFast: [WAKEUP] Đã gửi lệnh đánh thức TCU — chờ xe thức để lấy toạ độ.")
            return True

        _LOGGER.warning("VinFast: [WAKEUP] bị từ chối — HTTP %s code=%s", status, code)
        return False

    def _merge_telemetry_response(self, res):
        """[2.9.52] Gộp giá trị từ response `telemetry/app/ping` vào `core._last_data`.

        Vì sao tồn tại: T-Box chia dữ liệu thành 3 làn (đo 2026-09-20 khi xe chạy):
          * làn NHANH  3,00 s — chỉ 3 key: vĩ độ, kinh độ, TỐC ĐỘ (đẩy qua MQTT)
          * làn CHẬM  60,25 s — ~34 key `34193_*`
          * làn THEO THAY ĐỔI  — vị trí cần số, ODO, SOC, quãng đường: chỉ đẩy khi ĐỔI
        Nhóm thứ ba có thể im lặng suốt chuyến đi, nhưng `ping` luôn trả về giá trị mới nhất
        của server. Không parse response = mất nhóm này.

        Chỉ ghi đè khi `lastUpdateTime` MỚI HƠN giá trị đang giữ, để không làm cũ đi dữ liệu
        MQTT vốn tươi hơn nhiều (tốc độ: MQTT cũ 2,08 s vs ping cũ 33–108 s).
        """
        try:
            if res is None or getattr(res, "status_code", 0) != 200:
                # [2.9.53] Việc BÁO cho người dùng đã chuyển sang `register_resources()`
                # (chỉ báo 1 lần rồi tự chặn thử lại 30 phút). Ở đây chỉ ghi DEBUG để
                # không nhân đôi cảnh báo.
                _LOGGER.debug("VinFast: [TELEMETRY-PING] bỏ qua response HTTP %s",
                              getattr(res, "status_code", None))
                return 0
            data = (res.json() or {}).get("data") or []
        except Exception:
            return 0

        lut_map = getattr(self.core, "_telemetry_lut", None)
        if not isinstance(lut_map, dict):
            lut_map = {}
            self.core._telemetry_lut = lut_map

        changed = 0
        for item in data:
            if not isinstance(item, dict):
                continue
            key = item.get("deviceKey")
            if not key:
                continue
            raw_lut = item.get("lastUpdateTime")
            try:
                lut = int(raw_lut) if raw_lut is not None else 0
            except (TypeError, ValueError):
                lut = 0
            if lut and lut <= lut_map.get(key, 0):
                continue                      # cũ hơn hoặc bằng -> bỏ
            val = item.get("value")
            if val is None:
                continue
            if lut:
                lut_map[key] = lut
            if self.core._last_data.get(key) != val:
                self.core._last_data[key] = val
                changed += 1

        # [2.9.54] WARNING -> DEBUG: trace thông tin, không phải cảnh báo.
        if data and not getattr(self, "_merge_logged", False):
            self._merge_logged = True
            _LOGGER.debug(
                "VinFast: [TELEMETRY-PING] nhận %s key từ response ping, cập nhật %s key "
                "(nhóm 'theo thay đổi': vị trí cần số/ODO/SOC/quãng đường)",
                len(data), changed)

        # [2.9.57] Ping cũng mang toạ độ (00006_00001_00000/00001). Trước đây chỉ MQTT
        # mới ghi api_last_lat/api_last_lon nên xe ĐỖ (TCU ngủ, không có MQTT) không bao
        # giờ có `api_last_lat` dù server đã trả toạ độ trong response ping.
        # Đồng bộ để device_tracker, sensor và trip-debug dùng chung một nguồn.
        try:
            raw_lat = self.core._last_data.get("00006_00001_00000")
            raw_lon = self.core._last_data.get("00006_00001_00001")
            if raw_lat is not None and raw_lon is not None:
                flat, flon = float(raw_lat), float(raw_lon)
                if (-90.0 <= flat <= 90.0 and -180.0 <= flon <= 180.0
                        and (flat != 0.0 or flon != 0.0)):
                    if (self.core._last_data.get("api_last_lat") != flat
                            or self.core._last_data.get("api_last_lon") != flon):
                        self.core._last_data["api_last_lat"] = flat
                        self.core._last_data["api_last_lon"] = flon
                        self.core._last_lat_lon = f"{flat},{flon}"
                        changed += 1
                        _LOGGER.info(
                            "VinFast: [TELEMETRY-PING] cập nhật toạ độ từ ping: %.6f, %.6f",
                            flat, flon)
        except (TypeError, ValueError):
            pass

        if changed:
            _LOGGER.debug("VinFast: [TELEMETRY-PING] gộp %s key mới từ response ping", changed)
            self.core.trigger_callbacks()
        return changed

    def _control_credentials(self):
        """Đọc thông tin pairing phục vụ ký lệnh điều khiển từ options của config entry."""
        from .remote_control import DEFAULT_WAKEUP_TIMEOUT_MS, ControlCredentials

        options = getattr(self.core, "options", {}) or {}

        def _opt(key, default=""):
            value = options.get(key, default)
            return default if value is None else value

        def _flag(key, default=True):
            value = _opt(key, default)
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)

        try:
            wakeup_timeout_ms = int(_opt("control_wakeup_timeout_ms", DEFAULT_WAKEUP_TIMEOUT_MS))
        except (TypeError, ValueError):
            wakeup_timeout_ms = DEFAULT_WAKEUP_TIMEOUT_MS

        return ControlCredentials(
            user_id=str(getattr(self.core, "user_id", "") or self.core.email or ""),
            session_id=str(_opt("control_session_id", "")),
            private_key_pem=self._control_private_key_pem(_opt("control_private_key_pem", "")),
            share_key=str(_opt("control_share_key", "")) or None,
            is_master_profile=_flag("control_master_profile", True),
            wakeup_timeout_ms=wakeup_timeout_ms,
        )

    def _control_private_key_pem(self, configured_pem: str) -> str:
        """Chọn khoá RSA để ký lệnh điều khiển.

        Thứ tự ưu tiên:
        1. `control_private_key_pem` trong Options (khoá riêng cho điều khiển).
        2. Khoá RSA đã nạp cho component (`vinfast_private_key` trong Options,
           hoặc file `vinfast_private.pem` đi kèm) — đây là khoá người dùng đang dùng.

        Trả về chuỗi rỗng nếu không có khoá nào, khi đó `send_remote_command`
        sẽ fail-closed và ghi log.
        """
        if str(configured_pem or "").strip():
            return str(configured_pem)

        key = getattr(self.core, "private_key", None)
        if key is None and hasattr(self.core, "_load_private_key"):
            self.core._load_private_key()
            key = getattr(self.core, "private_key", None)
        if key is None:
            return ""

        try:
            from .remote_control import serialize_private_key_pem

            return serialize_private_key_pem(key)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VinFast: Không đọc được khoá RSA đã nạp cho điều khiển - %s", err)
            return ""

    async def send_remote_command(self, command, params=None):
        """Gửi lệnh điều khiển theo đúng giao thức v2 của VinFast.

        Không bao giờ gửi body thiếu ``signature``: nếu chưa có thông tin pairing
        (khoá riêng RSA + session id) thì dừng lại và ghi log lý do.

        [LEGACY v2.9.45 - giữ lại để tham chiếu/rollback, KHÔNG dùng]
        Bản cũ dựng payload::

            {"commandType": <int 1..20>, "vinCode": ..., "userId": ...,
             "sessionId": str(uuid4()), "timestamp": ms,
             "messageContent": {...}, "params": {}}

        Payload này không khớp `RemoteDataRequest` của APK và thiếu `signature`,
        nên server luôn từ chối. Xem DIEU_KHIEN_REMOTE_CONTROL.md muc 8.
        Bản đầy đủ nằm tại backups/2.9.46/api_auth.py.
        """
        from .remote_control import (
            RemoteControlError,
            build_remote_command_payload,
            explain_error_code,
            parse_command_response,
            resolve_command,
        )

        try:
            spec = resolve_command(command)
        except RemoteControlError as err:
            _LOGGER.error("VinFast: Lệnh điều khiển không hợp lệ - %s", err)
            return False

        merged_params = dict(params or {})
        merged_params.setdefault("vehicle_model", getattr(self.core, "vehicle_model_display", ""))

        try:
            payload = build_remote_command_payload(spec, self._control_credentials(), merged_params)
        except RemoteControlError as err:
            _LOGGER.error(
                "VinFast: Không gửi được lệnh '%s' (%s) - %s. "
                "Khoá RSA được lấy tự động từ tuỳ chọn 'control_private_key_pem' hoặc khoá đã nạp "
                "của component (vinfast_private_key / vinfast_private.pem). "
                "Lệnh chỉ chạy được sau khi tài khoản/xe đã hoàn tất kích hoạt điều khiển từ xa.",
                spec.name, spec.use_case, err,
            )
            return False

        # [2.9.54] WARNING -> INFO: gửi lệnh là hành động bình thường, không phải cảnh báo.
        _LOGGER.info(
            "VinFast: [CONTROL] Gửi lệnh '%s' use_case=%s message_name=%s timestamp=%s",
            spec.name, spec.use_case, payload.get("message_name"), payload.get("timestamp"),
        )
        res = await self.api_request("POST", "/ccaraccessmgmt/api/v2/remote/app/command", payload)
        if not res:
            _LOGGER.error("VinFast: Lệnh '%s' không nhận được phản hồi từ máy chủ.", spec.name)
            return False

        try:
            body = res.json() or {}
        except Exception:
            body = {}

        ok, control_error_code, message = parse_command_response(body)
        if res.status_code in (200, 201, 202, 204) and ok:
            # [2.9.54] WARNING -> INFO: thành công là chuyện thường.
            _LOGGER.info("VinFast: Lệnh '%s' (%s) đã được gửi thành công.", spec.name, spec.use_case)
            # Đánh thức telemetry để trạng thái xe cập nhật sớm sau khi điều khiển.
            self.core.hass.async_create_task(self.register_resources())
            return True

        _LOGGER.error(
            "VinFast: Lệnh '%s' bị từ chối - HTTP %s code=%s control_errorcode=%s message=%s%s",
            spec.name, res.status_code, body.get("code") if isinstance(body, dict) else None,
            control_error_code, message,
            (
                " | " + explain_error_code(body.get("code"))
                if isinstance(body, dict) and explain_error_code(body.get("code"))
                else ""
            ),
        )
        return False

    async def fetch_nearby_stations(self, force=True):
        try:
            now = time.time()
            if not force and now - getattr(self.core, '_last_station_fetch_time', 0) < 60: return

            lat_str = getattr(self.core, '_last_lat_lon', "").split(',')[0] if getattr(self.core, '_last_lat_lon', "") else self.core._last_data.get("api_last_lat")
            lon_str = getattr(self.core, '_last_lat_lon', "").split(',')[1] if getattr(self.core, '_last_lat_lon', "") else self.core._last_data.get("api_last_lon")
            if not lat_str or not lon_str: return
            
            payload = {"latitude": float(lat_str), "longitude": float(lon_str), "excludeFavorite": False}
            res = await self.api_request("POST", "/ccarcharging/api/v1/stations/search?page=0&size=20", payload)
            
            if res and res.status_code == 200:
                self.core._last_station_fetch_time = now
                stations = res.json().get("data", [])
                st_list = []
                for st in stations:
                    powers = st.get("evsePowers", [])
                    power_details = []
                    max_power = 0
                    avail_sum = st.get("numberOfAvailableEvse", 0)
                    total_sum = st.get("totalEvse", 0)
                    
                    for p in powers:
                        kw = int(p.get("type", 0) / 1000)
                        if kw > max_power: max_power = kw
                        p_avail = p.get("numberOfAvailableEvse", 0)
                        p_total = p.get("totalEvse", 0)
                        power_details.append(f"{kw}kW: {p_avail}/{p_total}")
                        
                    status = st.get("depotStatus", "Unknown")
                    status_vn = "Hoạt động" if status == "Available" else "Bảo trì/Hết chỗ"
                    
                    st_list.append({
                        "id": st.get("locationId", ""), "name": st.get("stationName", "Trạm Sạc"),
                        "lat": st.get("latitude"), "lng": st.get("longitude"), "dist": 0.0, 
                        "power": max_power, "avail": avail_sum, "total": total_sum,
                        "status": status_vn, "details": " | ".join(power_details)
                    })
                    
                self.core._last_data["api_nearby_stations"] = json.dumps(st_list, ensure_ascii=False)
                _LOGGER.info(f"VinFast: Đã tải thành công {len(st_list)} trạm sạc quanh vị trí.")
                self.core.trigger_callbacks()
        except Exception as e: 
            _LOGGER.error(f"VinFast: Lỗi tải trạm sạc - {e}")

    def fetch_active_charging_session(self): return False

    async def fetch_driving_trend(self, period_days=30):
        """Lấy dữ liệu xu hướng lái xe từ API VinFast.
        
        API: GET /ccaraccessmgmt/api/v1/c-app/driving-trend/info
        Params: vinCode, startTime (unix), endTime (unix)
        
        period_days: 7, 30, hoặc 365
        Trả về dict chứa distance_km, energy_kwh, efficiency_kwh_100km hoặc None nếu thất bại.
        """
        try:
            if not self.core.vin: return None
            import time as _time
            from datetime import datetime
            now = datetime.now()
            # Cần căn thời gian về đúng mốc giờ (phút=0, giây=0) vì VinFast API báo "The start time is not the beginning of the hour"
            aligned_now = now.replace(minute=0, second=0, microsecond=0)
            end_ts = int(aligned_now.timestamp())
            start_ts = end_ts - (period_days * 86400)
            
            res = await self.api_request(
                "GET",
                f"/ccaraccessmgmt/api/v1/c-app/driving-trend/info",
                params={"vinCode": self.core.vin, "startTime": start_ts, "endTime": end_ts}
            )
            
            if not res or res.status_code != 200:
                _LOGGER.warning(f"VinFast: [DRIVING-TREND] API {period_days}d thất bại: status={getattr(res,'status_code',None)}")
                return None
            
            data = res.json()
            # API trả về data trong trường "data" hoặc trực tiếp
            payload = data.get("data", data)
            
            if not payload:
                return None
            
            # Thử các key phổ biến từ VinFast API. Dữ liệu thực trả về: {"days": [{"time": ..., "distance": 21.0, "fuel": 1.97}, ...]}
            total_dist_km = 0.0
            total_energy_kwh = 0.0
            
            # Kiểm tra nếu payload là object có thuộc tính 'days'
            days_list = payload.get("days", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
            
            if days_list:
                for item in days_list:
                    total_dist_km += float(item.get("distance", item.get("totalDistance", item.get("km", 0))) or 0)
                    total_energy_kwh += float(item.get("fuel", item.get("totalEnergy", item.get("energyConsumed", 0))) or 0)
            elif isinstance(payload, dict):
                total_dist_km = float(payload.get("distance", payload.get("totalDistance", payload.get("totalKm", 0))) or 0)
                total_energy_kwh = float(payload.get("fuel", payload.get("totalEnergy", payload.get("energyConsumed", 0))) or 0)
            
            # Convert m → km nếu cần (nếu số quá lớn)
            if total_dist_km > 100000:
                total_dist_km = total_dist_km / 1000.0
            
            # Tính hiệu suất
            efficiency = None
            if total_dist_km > 0 and total_energy_kwh > 0:
                efficiency = round((total_energy_kwh / total_dist_km) * 100, 2)
            
            _LOGGER.info(
                f"VinFast: [DRIVING-TREND] {period_days}d: "
                f"dist={total_dist_km:.1f}km energy={total_energy_kwh:.1f}kWh "
                f"eff={efficiency} | raw={json.dumps(payload, ensure_ascii=False)[:200]}"
            )
            
            return {
                "period_days": period_days,
                "distance_km": round(total_dist_km, 1),
                "energy_kwh": round(total_energy_kwh, 2),
                "efficiency_kwh_100km": efficiency,
                "raw": payload
            }
            
        except Exception as e:
            _LOGGER.error(f"VinFast: [DRIVING-TREND] Lỗi fetch {period_days}d: {e}")
            return None

    async def fetch_all_driving_trends(self):
        """Lấy dữ liệu xu hướng lái xe cho 4 khoảng thời gian: 7 ngày, 30 ngày, 60 ngày, 1 năm.
        Lưu kết quả vào core._last_data và cache file.
        """
        try:
            results = {}
            for days in [7, 30, 60, 365]:
                r = await self.fetch_driving_trend(days)
                if r:
                    results[str(days)] = r
            
            if not results:
                _LOGGER.warning("VinFast: [DRIVING-TREND] Không lấy được bất kỳ dữ liệu nào")
                return False
            
            # Lưu vào _last_data để sensor có thể đọc
            self.core._last_data["api_driving_trend_json"] = json.dumps(results, ensure_ascii=False)
            
            # Tính hiệu suất trung bình vòng đời từ data 1 năm (ưu tiên) hoặc 30 ngày
            for period in ["365", "30", "7"]:
                if period in results and results[period].get("efficiency_kwh_100km"):
                    eff = results[period]["efficiency_kwh_100km"]
                    # Chỉ cập nhật nếu trong dải hợp lý
                    if 5.0 <= eff <= 40.0:
                        # Ưu tiên tính từ data 365 ngày để làm lifetime efficiency
                        if period == "365":
                            self.core._last_data["api_lifetime_efficiency"] = eff
                        break
            
            # Lưu cache file
            cache_file = os.path.join(self.core.storage_dir, f"vinfast_driving_trend_{self.core.vin.lower()}.json")
            import time as _time
            cache_data = {
                "metadata": {"last_fetch_time": _time.time(), "vin": self.core.vin},
                "trends": results
            }
            try:
                def _write():
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False)
                if hasattr(self.core, "hass") and self.core.hass:
                    await self.core.hass.async_add_executor_job(_write)
                else:
                    _write()
                _LOGGER.info(f"VinFast: [DRIVING-TREND] ✅ Đã lưu cache xu hướng lái xe ({len(results)} kỳ)")
            except Exception as e:
                _LOGGER.warning(f"VinFast: [DRIVING-TREND] Lỗi lưu cache: {e}")
            
            self.core.trigger_callbacks()
            return True
            
        except Exception as e:
            _LOGGER.error(f"VinFast: [DRIVING-TREND] Lỗi tổng hợp: {e}")
            return False

    async def fetch_full_driving_distance(self):
        try:
            if not self.core.vin: return 0.0
            import time as _time
            from datetime import datetime
            import json
            
            cache_file = os.path.join(self.core.storage_dir, f"vinfast_odo_fallback_{self.core.vin.lower()}.json")
            try:
                def _read_cache():
                    if not os.path.exists(cache_file):
                        return None
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                cache = await self.core.hass.async_add_executor_job(_read_cache)
                if cache:
                    last_fetch = cache.get("metadata", {}).get("last_fetch_time", 0)
                    if _time.time() - last_fetch < 43200:
                        est = cache.get("odo_estimate", 0.0)
                        self.core._last_data["api_odo_fallback_estimate"] = est
                        self.core._last_data["api_odo_fallback_source"] = "Cache lịch sử lái xe"
                        _LOGGER.info(f"VinFast: [ODO-FALLBACK] Dùng cache ODO fallback: {est:.1f} km")
                        return est
            except Exception:
                _LOGGER.debug("VinFast: không thể đọc ODO fallback cache", exc_info=True)

            # [2.9.55] WARNING -> DEBUG: trace tiến trình, không phải cảnh báo.
            _LOGGER.debug("VinFast: [ODO-FALLBACK] Mở rộng lịch sử từng năm tới khi tổng quãng đường không đổi...")
            aligned_now = datetime.now().replace(minute=0, second=0, microsecond=0)
            total_dist_km = 0.0
            previous_total = None
            scanned_years = 0
            max_years = 30

            for years in range(1, max_years + 1):
                try:
                    start_dt = aligned_now.replace(year=aligned_now.year - years)
                except ValueError:
                    start_dt = aligned_now.replace(year=aligned_now.year - years, month=2, day=28)
                end_ts = int(aligned_now.timestamp())
                start_ts = int(start_dt.timestamp())
                
                res = await self.api_request(
                    "GET",
                    f"/ccaraccessmgmt/api/v1/c-app/driving-trend/info",
                    params={"vinCode": self.core.vin, "startTime": start_ts, "endTime": end_ts}
                )
                if res and res.status_code == 200:
                    payload = res.json().get("data", res.json())
                    days_list = payload.get("days", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
                    current_total = 0.0
                    if days_list:
                        for item in days_list:
                            current_total += float(item.get("distance", item.get("totalDistance", item.get("km", 0))) or 0)
                    elif isinstance(payload, dict):
                        current_total = float(payload.get("distance", payload.get("totalDistance", payload.get("totalKm", 0))) or 0)
                    if current_total > 100000:
                        current_total /= 1000.0
                    scanned_years = years
                    if distance_total_unchanged(previous_total, current_total):
                        total_dist_km = current_total
                        _LOGGER.info("VinFast: [ODO-FALLBACK] Dữ liệu ổn định sau %s năm: %.1f km", years, current_total)
                        break
                    previous_total = current_total
                    total_dist_km = current_total
                else:
                    _LOGGER.warning("VinFast: [ODO-FALLBACK] API lỗi ở cửa sổ %s năm; giữ kết quả %.1f km", years, total_dist_km)
                    break
                await asyncio.sleep(0.5)
                
            self.core._last_data["api_odo_fallback_estimate"] = round(total_dist_km, 1)
            self.core._last_data["api_odo_fallback_source"] = f"API lịch sử mở rộng {scanned_years} năm"
            
            cache_data = {
                "metadata": {"last_fetch_time": _time.time(), "vin": self.core.vin, "scanned_years": scanned_years},
                "odo_estimate": round(total_dist_km, 1)
            }
            try:
                def _write():
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False)
                await self.core.hass.async_add_executor_job(_write)
            except Exception:
                _LOGGER.warning("VinFast: không thể ghi ODO fallback cache", exc_info=True)
            
            self.core.trigger_callbacks()
            return total_dist_km
        except Exception as e:
            _LOGGER.error(f"VinFast: [ODO-FALLBACK] Lỗi quét: {e}")
            return 0.0


    def _load_charge_cache(self):
        """Đọc cache lịch sử sạc từ file. Trả về dict chuẩn hóa."""
        cache_file = os.path.join(self.core.storage_dir, f"vinfast_charge_history_{self.core.vin.lower()}.json")
        empty_cache = {"metadata": {"version": 2, "total_sessions": 0, "last_fetch_time": 0.0,
                                     "newest_session_time": 0.0, "oldest_session_time": 0.0,
                                     "total_kwh": 0.0, "vin": self.core.vin}, "sessions": []}
        if not os.path.exists(cache_file):
            return empty_cache
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Backward compat: format cũ là list thuần
            if isinstance(data, list):
                _LOGGER.info(f"VinFast: [CHARGE-CACHE] Chuyển đổi cache cũ ({len(data)} phiên) sang format mới")
                sessions = data
                total_kwh = sum(safe_float(s.get("kwh", 0)) for s in sessions)
                newest_time = 0.0
                oldest_time = 0.0
                # Phân tích thời gian từ trường "date" (dd/mm/yyyy HH:MM)
                times = []
                for s in sessions:
                    try:
                        dt = datetime.datetime.strptime(s.get("date", ""), "%d/%m/%Y %H:%M")
                        times.append(dt.timestamp())
                    except Exception:
                        _LOGGER.debug("VinFast: không thể parse mốc thời gian cache sạc", exc_info=True)
                if times:
                    newest_time = max(times)
                    oldest_time = min(times)
                return {"metadata": {"version": 2, "total_sessions": len(sessions),
                                     "last_fetch_time": 0.0, "newest_session_time": newest_time,
                                     "oldest_session_time": oldest_time, "total_kwh": total_kwh,
                                     "vin": self.core.vin}, "sessions": sessions}
            # Format mới: dict với metadata
            if "metadata" in data and "sessions" in data:
                return data
        except Exception as e:
            _LOGGER.warning(f"VinFast: [CHARGE-CACHE] Lỗi đọc cache: {e}")
        return empty_cache

    def _save_charge_cache(self, cache):
        """Ghi cache lịch sử sạc ra file."""
        cache_file = os.path.join(self.core.storage_dir, f"vinfast_charge_history_{self.core.vin.lower()}.json")
        try:
            os.makedirs(self.core.storage_dir, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            _LOGGER.error(f"VinFast: [CHARGE-CACHE] Lỗi ghi cache: {e}")

    async def fetch_charging_history(self):
        """Tải lịch sử sạc với incremental cache.
        - Lần đầu (cache trống): Full fetch tất cả trang
        - Các lần sau: Chỉ fetch trang mới cho đến khi gặp session đã có trong cache
        """
        try:
            if not self.core.vin: return False

            PAGE_SIZE = 20
            MAX_PAGES = 20  # Tối đa 400 phiên mỗi lần full fetch

            # 1. Đọc cache hiện tại
            def _load():
                return self._load_charge_cache()
            cache = await self.core.hass.async_add_executor_job(_load)

            existing_sessions = cache.get("sessions", [])
            metadata = cache.get("metadata", {})
            newest_cached_time = metadata.get("newest_session_time", 0.0)
            is_first_run = len(existing_sessions) == 0

            if is_first_run:
                _LOGGER.info("VinFast: [CHARGE-CACHE] Cache trống – bắt đầu FULL FETCH tất cả lịch sử sạc...")
            else:
                _LOGGER.info(f"VinFast: [CHARGE-CACHE] Cache có {len(existing_sessions)} phiên, newest={newest_cached_time:.0f} – chế độ INCREMENTAL")

            # 2. Fetch từ API (phân trang)
            new_sessions_raw = []
            reached_cached_data = False
            page = 0

            while page < MAX_PAGES:
                payload = {"orderStatus": [3, 5, 7]}
                res = await self.api_request(
                    "POST",
                    f"/ccarcharging/api/v1/charging-sessions/search?page={page}&size={PAGE_SIZE}",
                    body_dict=payload
                )

                if not res or res.status_code != 200:
                    _LOGGER.warning(f"VinFast: [CHARGE-CACHE] API trang {page} thất bại, dừng fetch")
                    break

                data = res.json()
                api_sessions = data.get("data", [])

                if page == 0:
                    total_records = data.get("metadata", {}).get("totalRecords", len(api_sessions))
                    self.core._last_data["api_public_charge_sessions"] = total_records
                    _LOGGER.info(f"VinFast: [CHARGE-CACHE] Server có tổng {total_records} phiên sạc")

                if not api_sessions:
                    break

                # Parse sessions từ API response
                for s in api_sessions:
                    start_ts = s.get("startChargeTime", 0) / 1000.0
                    end_ts = s.get("endChargeTime", 0) / 1000.0

                    # Nếu không phải full fetch và đã gặp session cũ hơn cache → dừng
                    if not is_first_run and start_ts > 0 and start_ts <= newest_cached_time:
                        reached_cached_data = True
                        break

                    if start_ts > 0:
                        dt_obj = datetime.datetime.fromtimestamp(start_ts)
                        date_str = dt_obj.strftime("%d/%m/%Y %H:%M")
                    else:
                        date_str = "Unknown"

                    dur_mins = int((end_ts - start_ts) / 60) if end_ts > start_ts else 0
                    kwh = safe_float(s.get("totalKWCharged", 0))

                    new_sessions_raw.append({
                        "date": date_str,
                        "address": s.get("chargingStationAddress", "Trạm sạc VinFast"),
                        "kwh": kwh,
                        "duration": dur_mins,
                        "cost": safe_float(s.get("finalAmount", s.get("amount", 0))),
                        "session_time": start_ts
                    })

                if reached_cached_data:
                    _LOGGER.info(f"VinFast: [CHARGE-CACHE] Đã đến dữ liệu cũ ở trang {page} – dừng incremental")
                    break

                if len(api_sessions) < PAGE_SIZE:
                    break  # Hết trang

                page += 1

            # 3. Merge: new sessions + existing cache (tránh trùng lặp theo session_time)
            existing_times = {s.get("session_time", 0) for s in existing_sessions}
            truly_new = [s for s in new_sessions_raw if s.get("session_time", 0) not in existing_times]

            merged_sessions = truly_new + existing_sessions  # Mới nhất ở đầu

            # 4. Tính tổng kWh từ toàn bộ cache
            total_public_kwh = sum(safe_float(s.get("kwh", 0)) for s in merged_sessions)
            home_kwh = safe_float(self.core._last_data.get("api_home_charge_kwh", 0))
            total_kwh = total_public_kwh + home_kwh

            # 5. Cập nhật metadata
            newest_time = max((s.get("session_time", 0) for s in merged_sessions), default=0.0)
            oldest_time = min((s.get("session_time", 0) for s in merged_sessions if s.get("session_time", 0) > 0), default=0.0)

            updated_cache = {
                "metadata": {
                    "version": 2,
                    "total_sessions": len(merged_sessions),
                    "last_fetch_time": time.time(),
                    "newest_session_time": newest_time,
                    "oldest_session_time": oldest_time,
                    "total_kwh": round(total_public_kwh, 2),
                    "vin": self.core.vin
                },
                "sessions": merged_sessions
            }

            # 6. Lưu cache đầy đủ ra file
            def _save():
                self._save_charge_cache(updated_cache)
            await self.core.hass.async_add_executor_job(_save)

            # 7. Cập nhật sensors
            current_total = safe_float(self.core._last_data.get("api_total_energy_charged", 0))
            if total_kwh > current_total:
                self.core._last_data["api_total_energy_charged"] = round(total_kwh, 2)

            # Chỉ đẩy 20 phiên gần nhất lên api_charge_history_list (cho Lovelace card)
            recent_20 = merged_sessions[:20]
            self.core._last_data["api_charge_history_list"] = json.dumps(recent_20, ensure_ascii=False)

            _LOGGER.info(
                f"VinFast: [CHARGE-CACHE] ✅ Tổng cache: {len(merged_sessions)} phiên "
                f"(+{len(truly_new)} mới) | {total_public_kwh:.1f} kWh công + {home_kwh:.1f} kWh nhà "
                f"= {total_kwh:.1f} kWh vòng đời"
            )

            self.core.trigger_callbacks()
            return True

        except Exception as e:
            _LOGGER.error(f"VinFast: [CHARGE-CACHE] Lỗi fetch lịch sử sạc: {e}")
        return False
