import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_AI_BASE_URL,
    CONF_AI_API_KEY,
    CONF_AI_MODEL,
    CONF_REGION,
    CONF_LANGUAGE,
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_MODEL,
)
from .api import VinFastAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    email = entry.data.get(CONF_EMAIL, entry.data.get("email"))
    password = entry.data.get(CONF_PASSWORD, entry.data.get("password"))
    
    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION, "VN"))
    lang = entry.options.get(CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, "vi"))
    ai_base_url = entry.options.get(CONF_AI_BASE_URL, entry.data.get(CONF_AI_BASE_URL, DEFAULT_AI_BASE_URL))
    ai_api_key = entry.options.get(CONF_AI_API_KEY, entry.data.get(CONF_AI_API_KEY, ""))
    ai_model = entry.options.get(CONF_AI_MODEL, entry.data.get(CONF_AI_MODEL, DEFAULT_AI_MODEL))

    api = VinFastAPI(
        email,
        password,
        region=region,
        lang=lang,
        ai_base_url=ai_base_url,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
        options=entry.options,
    )
    api.hass = hass
    logged_in = await hass.async_add_executor_job(api.login)
    if not logged_in:
        _LOGGER.error("VinFast: Đăng nhập thất bại.")
        return False
    
    vehicles = await hass.async_add_executor_job(api.get_vehicles)
    if not vehicles:
        _LOGGER.error("VinFast: Không tìm thấy xe.")
        return False

    hass.data[DOMAIN][entry.entry_id] = {"api": api}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    def start_mqtt_thread():
        api.start_mqtt()
        
    await hass.async_add_executor_job(start_mqtt_thread)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data[DOMAIN].pop(entry.entry_id)
        api = domain_data.get("api")
        if api:
            await hass.async_add_executor_job(api.stop)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("VinFast: Cập nhật cấu hình, nạp lại...")
    await hass.config_entries.async_reload(entry.entry_id)
