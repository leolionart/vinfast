import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import logging
import requests

from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import (
    DOMAIN, 
    CONF_EMAIL, 
    CONF_PASSWORD, 
    CONF_GEMINI_API_KEY, 
    CONF_REGION, 
    CONF_LANGUAGE,
    CONF_MAPBOX_TOKEN,
    CONF_STADIA_TOKEN,
)
try:
    from .const import (
        CONF_UAA_CLIENT_INSTANCE_ID,
        CONF_UAA_SIGNATURE,
        CONF_UAA_TIMESTAMP,
        CONF_VINFAST_PRIVATE_KEY,
        # [2.9.60] Máy chủ MQTT cho phép ghi đè từ UI (VinFast đổi máy chủ thì
        # không phải sửa code rồi khởi động lại HA).
        CONF_EMQX_HOST,
        CONF_EMQX_PORT,
        emqx_server,
    )
except ImportError:
    CONF_UAA_CLIENT_INSTANCE_ID = "uaa_client_instance_id"
    CONF_UAA_SIGNATURE = "uaa_signature"
    CONF_UAA_TIMESTAMP = "uaa_timestamp"
    CONF_VINFAST_PRIVATE_KEY = "vinfast_private_key"
    CONF_EMQX_HOST = "emqx_host"
    CONF_EMQX_PORT = "emqx_port"

    def emqx_server(region="VN", options=None):
        """Dự phòng khi const.py bản cũ chưa có hàm này."""
        return "ccp-mqtt.vinfast.vn", 8884

_LOGGER = logging.getLogger(__name__)

CONF_GEMINI_MODEL = "gemini_model"

REGIONS = {"VN": "Việt Nam (VN)", "US": "United States (US)"}
LANGUAGES = {"vi": "Tiếng Việt (VI)", "en": "English (EN)"}

def safe_int(val, default):
    try: return int(float(val))
    except (ValueError, TypeError): return default

# =====================================================================
# THUẬT TOÁN TỰ ĐỘNG QUÉT DANH SÁCH MODEL MỚI NHẤT TỪ GOOGLE GEMINI
# =====================================================================
def fetch_gemini_models_sync(api_key):
    # Danh sách dự phòng nếu mạng lỗi hoặc người dùng không nhập Key
    default_models = {
        "gemini-2.5-flash": "Gemini 2.5 Flash (Khuyên dùng/Nhanh/Free)",
        "gemini-2.5-pro": "Gemini 2.5 Pro (Cao cấp)",
        "gemini-2.0-flash": "Gemini 2.0 Flash (Nhanh/Free)",
        "gemini-1.5-flash": "Gemini 1.5 Flash",
    }
    
    if not api_key or str(api_key).strip() == "":
        return default_models
        
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            models = {}
            
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                display = m.get("displayName", name)
                methods = m.get("supportedGenerationMethods", [])
                
                # Chỉ lấy các model sinh text (Bỏ qua model nhúng/âm thanh/cũ)
                if "generateContent" in methods and "gemini" in name.lower() and "vision" not in name.lower():
                    # Gắn tag phân loại thông minh
                    if "flash" in name.lower():
                        display = f"{display} (Nhanh/Free)"
                    elif "pro" in name.lower():
                        display = f"{display} (Cao cấp)"
                    
                    models[name] = display
            
            if models:
                # Thuật toán Sắp xếp: Ưu tiên bản 2.5 lên đầu -> Đến dòng Flash -> Các dòng khác
                sorted_models = dict(sorted(models.items(), key=lambda item: (
                    not ("2.5" in item[0]), 
                    not ("flash" in item[0]), 
                    item[0]
                )))
                return sorted_models
                
    except Exception as e:
        _LOGGER.error(f"VinFast: Lỗi khi lấy danh sách Gemini models động: {e}")
        
    return default_models

class VinFastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._setup_data = {}

    async def async_step_user(self, user_input=None):
        # BƯỚC 1: NHẬP TÀI KHOẢN VÀ CÁC API KEY
        if user_input is not None:
            if CONF_EMAIL in user_input:
                user_input[CONF_EMAIL] = str(user_input[CONF_EMAIL]).strip()
            if CONF_PASSWORD in user_input:
                user_input[CONF_PASSWORD] = str(user_input[CONF_PASSWORD]).strip()
            self._setup_data.update(user_input)
            return await self.async_step_model()

        # Bổ sung Mapbox và Stadia vào Form khởi tạo
        data_schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_UAA_CLIENT_INSTANCE_ID): str,
            vol.Required(CONF_UAA_SIGNATURE): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_UAA_TIMESTAMP): str,
            # Private key is optional on first install – if omitted the integration will attempt
            # to load `vinfast_private.pem` from the component folder (handled in __init__.py).
            vol.Optional(CONF_VINFAST_PRIVATE_KEY, default=""): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, multiline=True)),
            vol.Required(CONF_REGION, default="VN"): vol.In(REGIONS),
            vol.Required(CONF_LANGUAGE, default="vi"): vol.In(LANGUAGES),
            vol.Optional(CONF_GEMINI_API_KEY, default=""): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional(CONF_MAPBOX_TOKEN, default=""): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional(CONF_STADIA_TOKEN, default=""): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        })
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_model(self, user_input=None):
        # BƯỚC 2: TỰ ĐỘNG LOAD MODEL VÀ CHỐT LƯU
        if user_input is not None:
            self._setup_data.update(user_input)
            await self.async_set_unique_id(self._setup_data[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=self._setup_data[CONF_EMAIL], data=self._setup_data)

        api_key = self._setup_data.get(CONF_GEMINI_API_KEY, "")
        
        # Chạy ngầm hàm lấy API để không làm treo giao diện Home Assistant
        models = await self.hass.async_add_executor_job(fetch_gemini_models_sync, api_key)
        
        data_schema = vol.Schema({
            vol.Required(CONF_GEMINI_MODEL, default=list(models.keys())[0]): vol.In(models),
        })
        return self.async_show_form(step_id="model", data_schema=data_schema)

    async def async_step_reconfigure(self, user_input=None):
        """Xử lý cấu hình lại tài khoản và mật khẩu."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if not entry:
            return self.async_abort(reason="reconfigure_failed")

        if user_input is not None:
            new_data = dict(entry.data)
            if CONF_EMAIL in user_input:
                user_input[CONF_EMAIL] = str(user_input[CONF_EMAIL]).strip()
            if CONF_PASSWORD in user_input:
                user_input[CONF_PASSWORD] = str(user_input[CONF_PASSWORD]).strip()
            new_data.update(user_input)
            self.hass.config_entries.async_update_entry(entry, data=new_data)
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        data = entry.data
        opts = entry.options
        current_email = data.get(CONF_EMAIL, "")
        current_password = data.get(CONF_PASSWORD, "")
        current_uaa_client_id = opts.get(CONF_UAA_CLIENT_INSTANCE_ID, data.get(CONF_UAA_CLIENT_INSTANCE_ID, ""))
        current_uaa_signature = opts.get(CONF_UAA_SIGNATURE, data.get(CONF_UAA_SIGNATURE, ""))
        current_uaa_timestamp = opts.get(CONF_UAA_TIMESTAMP, data.get(CONF_UAA_TIMESTAMP, ""))
        if not current_uaa_client_id:
            from . import const
            current_uaa_client_id = getattr(const, "UAA_CLIENT_INSTANCE_ID", "")
            current_uaa_signature = getattr(const, "UAA_SIGNATURE", "")
            current_uaa_timestamp = getattr(const, "UAA_TIMESTAMP", "")
        current_private_key = opts.get(CONF_VINFAST_PRIVATE_KEY, data.get(CONF_VINFAST_PRIVATE_KEY, ""))
        current_region = opts.get(CONF_REGION, data.get(CONF_REGION, "VN"))
        current_lang = opts.get(CONF_LANGUAGE, data.get(CONF_LANGUAGE, "vi"))

        reconfigure_schema = vol.Schema({
            vol.Required(CONF_EMAIL, default=current_email): str,
            vol.Required(CONF_PASSWORD, default=current_password): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_UAA_CLIENT_INSTANCE_ID, default=current_uaa_client_id): str,
            vol.Required(CONF_UAA_SIGNATURE, default=current_uaa_signature): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_UAA_TIMESTAMP, default=current_uaa_timestamp): str,
            vol.Required(CONF_VINFAST_PRIVATE_KEY, default=current_private_key): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, multiline=True)),
            vol.Required(CONF_REGION, default=current_region): vol.In(REGIONS),
            vol.Required(CONF_LANGUAGE, default=current_lang): vol.In(LANGUAGES),
        })
        return self.async_show_form(step_id="reconfigure", data_schema=reconfigure_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VinFastOptionsFlowHandler(config_entry)

class VinFastOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            if CONF_EMAIL in user_input:
                user_input[CONF_EMAIL] = str(user_input[CONF_EMAIL]).strip()
            if CONF_PASSWORD in user_input:
                user_input[CONF_PASSWORD] = str(user_input[CONF_PASSWORD]).strip()
            return self.async_create_entry(title="", data=user_input)

        opts = self._config_entry.options
        data = self._config_entry.data
        
        current_email = opts.get(CONF_EMAIL, data.get(CONF_EMAIL, ""))
        current_password = opts.get(CONF_PASSWORD, data.get(CONF_PASSWORD, ""))
        current_region = opts.get(CONF_REGION, data.get(CONF_REGION, "VN"))
        current_lang = opts.get(CONF_LANGUAGE, data.get(CONF_LANGUAGE, "vi"))
        current_gemini_key = opts.get(CONF_GEMINI_API_KEY, data.get(CONF_GEMINI_API_KEY, ""))
        current_gemini_model = opts.get(CONF_GEMINI_MODEL, data.get(CONF_GEMINI_MODEL, "gemini-2.5-flash"))
        current_mapbox = opts.get(CONF_MAPBOX_TOKEN, data.get(CONF_MAPBOX_TOKEN, ""))
        current_stadia = opts.get(CONF_STADIA_TOKEN, data.get(CONF_STADIA_TOKEN, ""))

        # Cập nhật lại danh sách Model mỗi khi người dùng bấm Cấu hình lại
        available_models = await self.hass.async_add_executor_job(fetch_gemini_models_sync, current_gemini_key)
        if current_gemini_model not in available_models:
            available_models[current_gemini_model] = current_gemini_model

        current_uaa_client_id = opts.get(CONF_UAA_CLIENT_INSTANCE_ID, data.get(CONF_UAA_CLIENT_INSTANCE_ID, ""))
        current_uaa_signature = opts.get(CONF_UAA_SIGNATURE, data.get(CONF_UAA_SIGNATURE, ""))
        current_uaa_timestamp = opts.get(CONF_UAA_TIMESTAMP, data.get(CONF_UAA_TIMESTAMP, ""))
        if not current_uaa_client_id:
            from . import const
            current_uaa_client_id = getattr(const, "UAA_CLIENT_INSTANCE_ID", "")
            current_uaa_signature = getattr(const, "UAA_SIGNATURE", "")
            current_uaa_timestamp = getattr(const, "UAA_TIMESTAMP", "")
        current_private_key = opts.get(CONF_VINFAST_PRIVATE_KEY, data.get(CONF_VINFAST_PRIVATE_KEY, ""))

        # --- Máy chủ MQTT: mặc định lấy từ const.py, người dùng có thể ghi đè ---
        default_emqx_host, default_emqx_port = emqx_server(current_region, opts)
        current_emqx_host = str(opts.get(CONF_EMQX_HOST)
                                or data.get(CONF_EMQX_HOST) or default_emqx_host)
        current_emqx_port = safe_int(
            opts.get(CONF_EMQX_PORT, data.get(CONF_EMQX_PORT, default_emqx_port)),
            default_emqx_port)

        # Bổ sung các cấu hình nâng cao vào Form
        options_schema = vol.Schema({
            vol.Required(CONF_EMAIL, default=current_email): str,
            vol.Required(CONF_PASSWORD, default=current_password): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_REGION, default=current_region): vol.In(REGIONS),
            vol.Required(CONF_LANGUAGE, default=current_lang): vol.In(LANGUAGES),
            vol.Optional(CONF_GEMINI_API_KEY, default=current_gemini_key): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_GEMINI_MODEL, default=current_gemini_model): vol.In(available_models),
            vol.Optional(CONF_MAPBOX_TOKEN, default=current_mapbox): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional(CONF_STADIA_TOKEN, default=current_stadia): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            # --- Máy chủ MQTT (để trống = dùng giá trị trong const.py) ---
            vol.Optional(CONF_EMQX_HOST, default=current_emqx_host): str,
            vol.Optional(CONF_EMQX_PORT, default=current_emqx_port): vol.Coerce(int),
            vol.Required("cost_per_kwh", default=safe_int(opts.get("cost_per_kwh"), 4000)): vol.Coerce(int),
            vol.Required("gas_price", default=safe_int(opts.get("gas_price"), 20000)): vol.Coerce(int),
            vol.Required(CONF_UAA_CLIENT_INSTANCE_ID, default=current_uaa_client_id): str,
            vol.Required(CONF_UAA_SIGNATURE, default=current_uaa_signature): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(CONF_UAA_TIMESTAMP, default=current_uaa_timestamp): str,
            vol.Required(CONF_VINFAST_PRIVATE_KEY, default=current_private_key): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, multiline=True)),
            # --- Điều khiển từ xa (pairing) ---
            vol.Optional("control_private_key_pem", default=opts.get("control_private_key_pem", "")): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, multiline=True)),
            vol.Optional("control_share_key", default=opts.get("control_share_key", "")): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional("control_session_id", default=opts.get("control_session_id", "")): str,
            vol.Optional("control_master_profile", default=bool(opts.get("control_master_profile", True))): bool,
            vol.Optional("control_wakeup_timeout_ms", default=safe_int(opts.get("control_wakeup_timeout_ms"), 30000)): vol.Coerce(int),
            # Bật thêm 32 nút lệnh mở rộng (capo, cửa sổ trời, SOC mục tiêu, lịch sạc,
            # lịch điều hoà, FOTA, các nhánh điều hoà) — mặc định tắt cho gọn UI.
            vol.Optional("control_advanced_buttons", default=bool(opts.get("control_advanced_buttons", False))): bool,
        })
        
        return self.async_show_form(step_id="init", data_schema=options_schema)
