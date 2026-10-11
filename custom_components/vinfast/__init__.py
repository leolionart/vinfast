import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (DOMAIN, CONF_EMAIL, CONF_PASSWORD,
                    CONF_GEMINI_API_KEY, CONF_REGION, CONF_LANGUAGE,
                    REGION_CONFIG, DEVICE_ID, DEVICE_ID_BY_EMAIL)
try:
    from .const import (
        CONF_UAA_CLIENT_INSTANCE_ID,
        CONF_UAA_SIGNATURE,
        CONF_UAA_TIMESTAMP,
        CONF_VINFAST_PRIVATE_KEY
    )
except ImportError:
    CONF_UAA_CLIENT_INSTANCE_ID = "uaa_client_instance_id"
    CONF_UAA_SIGNATURE = "uaa_signature"
    CONF_UAA_TIMESTAMP = "uaa_timestamp"
    CONF_VINFAST_PRIVATE_KEY = "vinfast_private_key"

from .api import VinFastAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button", "device_tracker"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    needs_update = False
    new_data = dict(entry.data)
    
    # ---------------------------------------------------------
    # 1. FAILSAFE AUTO-MIGRATE: Legacy PEM file sang config entry
    # ---------------------------------------------------------
    if CONF_VINFAST_PRIVATE_KEY not in new_data and CONF_VINFAST_PRIVATE_KEY not in entry.options:
        pem_path = os.path.join(os.path.dirname(__file__), "vinfast_private.pem")
        if os.path.isfile(pem_path):
            try:
                def read():
                    with open(pem_path, "r", encoding="utf-8") as f:
                        return f.read()
                pem = await hass.async_add_executor_job(read)
                if pem:
                    new_data[CONF_VINFAST_PRIVATE_KEY] = pem
                    needs_update = True
                    _LOGGER.info("VinFast [Failsafe]: Đã chuyển PEM file vào cấu hình hệ thống.")
            except Exception as e:
                _LOGGER.warning("VinFast [Failsafe]: Không thể đọc pem file - %s", e)

    # ---------------------------------------------------------
    # 2. FAILSAFE AUTO-MIGRATE: Tự động nhận diện UAA từ const.py cũ
    # ---------------------------------------------------------
    from . import const
    legacy_uaa_id = getattr(const, "UAA_CLIENT_INSTANCE_ID", "")
    legacy_uaa_sig = getattr(const, "UAA_SIGNATURE", "")
    legacy_uaa_ts = getattr(const, "UAA_TIMESTAMP", "")
    if legacy_uaa_id and not new_data.get(CONF_UAA_CLIENT_INSTANCE_ID) and not entry.options.get(CONF_UAA_CLIENT_INSTANCE_ID):
        new_data[CONF_UAA_CLIENT_INSTANCE_ID] = str(legacy_uaa_id).strip()
        new_data[CONF_UAA_SIGNATURE] = str(legacy_uaa_sig).strip()
        new_data[CONF_UAA_TIMESTAMP] = str(legacy_uaa_ts).strip()
        needs_update = True
        _LOGGER.info("VinFast [Failsafe]: Tự động đồng bộ UAA credentials từ const.py cũ vào cấu hình.")

    if needs_update:
        hass.config_entries.async_update_entry(entry, data=new_data)

    # ---------------------------------------------------------
    # 3. FAILSAFE VALIDATE: Kiểm tra UAA (không chặn khởi động HA)
    # ---------------------------------------------------------
    missing_uaa = [
        key for key in (CONF_UAA_CLIENT_INSTANCE_ID, CONF_UAA_SIGNATURE, CONF_UAA_TIMESTAMP)
        if not entry.options.get(key, new_data.get(key))
    ]
    if missing_uaa:
        _LOGGER.warning("VinFast [Failsafe]: Chưa đủ thông tin UAA (%s). HA vẫn khởi động bình thường; vui lòng vào Cài đặt -> Tùy chọn để bổ sung.", ", ".join(missing_uaa))
        raise ConfigEntryNotReady(f"VinFast: Thiếu cấu hình UAA ({', '.join(missing_uaa)}), vui lòng cấu hình trong Tùy chọn.")

    email = entry.options.get(CONF_EMAIL, new_data.get(CONF_EMAIL, new_data.get("email")))
    password = entry.options.get(CONF_PASSWORD, new_data.get(CONF_PASSWORD, new_data.get("password")))
    
    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION, "VN"))
    lang = entry.options.get(CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, "vi"))
    gemini_key = entry.options.get(CONF_GEMINI_API_KEY, entry.data.get(CONF_GEMINI_API_KEY, ""))

    api = VinFastAPI(email, password, region=region, lang=lang, gemini_api_key=gemini_key, options=entry.options)
    api.hass = hass
    api.data = new_data

    # [2.9.59] [CONST-SYNC] In ra mọi giá trị HA KHÔNG THỂ TỰ LẤY, kèm nguồn.
    # Mục đích: khi const.py lệch với config entry / harvested_db thì thấy ngay trong
    # log thay vì đoán qua triệu chứng (sai device id -> ping 403 y như "xe đang ngủ").
    try:
        _rc = REGION_CONFIG.get(region) or REGION_CONFIG["VN"]
        _dev = api._device_id() if hasattr(api, "_device_id") else DEVICE_ID
        _opt_dev = str(entry.options.get("device_id") or entry.data.get("device_id") or "")
        _uaa = str(entry.options.get("uaa_client_instance_id")
                   or entry.data.get("uaa_client_instance_id") or "")
        _db_uaa = ""
        try:
            import json as _json
            with open("/home/pi/vinfast/harvested_db.json", encoding="utf-8") as _f:
                _db_uaa = str((_json.load(_f).get(str(email or "").lower()) or {})
                              .get("uaa_client_instance_id") or "")
        except Exception:
            pass
        _LOGGER.info(
            "VinFast: [CONST-SYNC] region=%s | API=%s | IOT=%s | EMQX=%s:%s | "
            "device_id=%s (const=%s, option=%s) | UAA=%s (entry=%s, db=%s)",
            region, _rc.get("API_BASE"), _rc.get("IOT_ENDPOINT"),
            _rc.get("EMQX_HOST"), _rc.get("EMQX_PORT"),
            _dev, (DEVICE_ID_BY_EMAIL or {}).get(str(email or "").lower(), DEVICE_ID),
            _opt_dev or "(không đặt)",
            (_uaa[:8] + "…") if _uaa else "(rỗng)",
            "khớp" if (_uaa and _db_uaa and _uaa == _db_uaa) else
            ("chỉ có ở entry" if _uaa and not _db_uaa else
             ("chỉ có ở db" if _db_uaa and not _uaa else
              ("KHỚP" if not _uaa and not _db_uaa else "LỆCH"))),
            (_db_uaa[:8] + "…") if _db_uaa else "(rỗng)",
        )
    except Exception as _exc:  # noqa: BLE001 — log không được làm hỏng setup
        _LOGGER.debug("VinFast: [CONST-SYNC] không dựng được dòng log: %s", _exc)
    
    # ---------------------------------------------------------
    # 4. FAILSAFE CONNECTIVITY: Bọc try-except không chặn HA
    # ---------------------------------------------------------
    try:
        await hass.async_add_executor_job(api._load_private_key)
        logged_in = await api.login()
    except Exception as exc:
        _LOGGER.warning("VinFast [Failsafe]: Lỗi kết nối máy chủ xác thực lúc khởi động (%s). Sẽ tự thử lại trong nền.", exc)
        logged_in = False

    if not logged_in:
        raise ConfigEntryNotReady("VinFast: Đăng nhập Auth0/UAA chưa sẵn sàng, hệ thống sẽ tự động thử lại trong nền...")
    
    try:
        vehicles = await api.get_vehicles()
    except Exception as exc:
        _LOGGER.warning("VinFast [Failsafe]: Lỗi lấy danh sách xe lúc khởi động (%s). Sẽ tự thử lại trong nền.", exc)
        vehicles = None

    if not vehicles:
        raise ConfigEntryNotReady("VinFast: Chưa lấy được danh sách xe, hệ thống sẽ tự động thử lại trong nền...")

    hass.data[DOMAIN][entry.entry_id] = {"api": api}

    # --- [dsh] Waze Mod: cảnh báo theo toạ độ xe (task nền, không chặn setup) ---
    try:
        from .waze_integration import async_setup_waze
        await async_setup_waze(hass, entry, api)
    except Exception as _waze_exc:  # noqa: BLE001
        _LOGGER.warning("VinFast Waze: không khởi động được (%s)", _waze_exc)

    
    # Đăng ký HTTP Views bảo mật (failsafe)
    try:
        from .views import (
            VinFastTripsView, 
            VinFastChargeHistoryView, 
            VinFastChangelogView, 
            VinFastStateView
        )
        if not hass.data[DOMAIN].get("_views_registered"):
            hass.http.register_view(VinFastTripsView(api))
            hass.http.register_view(VinFastChargeHistoryView(api))
            hass.http.register_view(VinFastChangelogView(api))
            hass.http.register_view(VinFastStateView(api))
            hass.data[DOMAIN]["_views_registered"] = True
    except Exception as e:
        _LOGGER.debug("VinFast [Failsafe]: HTTP views - %s", e)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    try:
        api.start_mqtt()
    except Exception as e:
        _LOGGER.warning("VinFast [Failsafe]: Không thể khởi động MQTT - %s", e)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        api = domain_data.get("api")
        if api:
            await hass.async_add_executor_job(api.stop)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("VinFast: Cập nhật cấu hình, nạp lại...")
    await hass.config_entries.async_reload(entry.entry_id)
