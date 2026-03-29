import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import logging

from .const import (
    DOMAIN, 
    CONF_EMAIL, 
    CONF_PASSWORD, 
    CONF_AI_BASE_URL,
    CONF_AI_API_KEY,
    CONF_AI_MODEL,
    CONF_REGION, 
    CONF_LANGUAGE,
    CONF_MAPBOX_TOKEN,
    CONF_STADIA_TOKEN,
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_MODEL,
)

_LOGGER = logging.getLogger(__name__)

REGIONS = {"VN": "Việt Nam (VN)", "US": "United States (US)", "EU": "Europe (EU)"}
LANGUAGES = {"vi": "Tiếng Việt (VI)", "en": "English (EN)"}

def safe_int(val, default):
    try: return int(float(val))
    except (ValueError, TypeError): return default

def normalize_ai_base_url(base_url):
    return (base_url or "").strip().rstrip("/")

class VinFastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._setup_data = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            user_input[CONF_AI_BASE_URL] = normalize_ai_base_url(user_input.get(CONF_AI_BASE_URL, DEFAULT_AI_BASE_URL))
            self._setup_data.update(user_input)
            await self.async_set_unique_id(self._setup_data[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=self._setup_data[CONF_EMAIL], data=self._setup_data)

        data_schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_REGION, default="VN"): vol.In(REGIONS),
            vol.Required(CONF_LANGUAGE, default="vi"): vol.In(LANGUAGES),
            vol.Optional(CONF_AI_BASE_URL, default=DEFAULT_AI_BASE_URL): str,
            vol.Optional(CONF_AI_API_KEY, default=""): str,
            vol.Optional(CONF_AI_MODEL, default=DEFAULT_AI_MODEL): str,
            vol.Optional(CONF_MAPBOX_TOKEN, default=""): str,
            vol.Optional(CONF_STADIA_TOKEN, default=""): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VinFastOptionsFlowHandler(config_entry)

class VinFastOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            user_input[CONF_AI_BASE_URL] = normalize_ai_base_url(user_input.get(CONF_AI_BASE_URL, DEFAULT_AI_BASE_URL))
            return self.async_create_entry(title="", data=user_input)

        opts = self._config_entry.options
        data = self._config_entry.data
        
        current_region = opts.get(CONF_REGION, data.get(CONF_REGION, "VN"))
        current_lang = opts.get(CONF_LANGUAGE, data.get(CONF_LANGUAGE, "vi"))
        current_ai_base_url = opts.get(CONF_AI_BASE_URL, data.get(CONF_AI_BASE_URL, DEFAULT_AI_BASE_URL))
        current_ai_api_key = opts.get(CONF_AI_API_KEY, data.get(CONF_AI_API_KEY, ""))
        current_ai_model = opts.get(CONF_AI_MODEL, data.get(CONF_AI_MODEL, DEFAULT_AI_MODEL))
        current_mapbox = opts.get(CONF_MAPBOX_TOKEN, data.get(CONF_MAPBOX_TOKEN, ""))
        current_stadia = opts.get(CONF_STADIA_TOKEN, data.get(CONF_STADIA_TOKEN, ""))

        options_schema = vol.Schema({
            vol.Required(CONF_REGION, default=current_region): vol.In(REGIONS),
            vol.Required(CONF_LANGUAGE, default=current_lang): vol.In(LANGUAGES),
            vol.Optional(CONF_AI_BASE_URL, default=current_ai_base_url): str,
            vol.Optional(CONF_AI_API_KEY, default=current_ai_api_key): str,
            vol.Optional(CONF_AI_MODEL, default=current_ai_model): str,
            vol.Optional(CONF_MAPBOX_TOKEN, default=current_mapbox): str,
            vol.Optional(CONF_STADIA_TOKEN, default=current_stadia): str,
            vol.Required("cost_per_kwh", default=safe_int(opts.get("cost_per_kwh"), 4000)): vol.Coerce(int),
            vol.Required("gas_price", default=safe_int(opts.get("gas_price"), 20000)): vol.Coerce(int),
        })
        
        return self.async_show_form(step_id="init", data_schema=options_schema)
