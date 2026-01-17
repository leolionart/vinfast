"""Constants for the VinFast integration."""

DOMAIN = "vinfast"

# Region configuration
CONF_REGION = "region"

REGION_US = "us"
REGION_EU = "eu"
REGION_VN = "vn"

REGIONS = {
    REGION_US: {
        "name": "United States",
        "auth0_domain": "vinfast-us-prod.us.auth0.com",
        "auth0_client_id": "xhGY7XKDFSk1Q22rxidvwujfz0EPAbUP",
        "auth0_audience": "https://vinfast-us-prod.us.auth0.com/api/v2/",
        "api_base": "https://mobile.connected-car.vinfastauto.us",
    },
    REGION_EU: {
        "name": "Europe",
        "auth0_domain": "vinfast-eu-prod.eu.auth0.com",
        "auth0_client_id": "dxxtNkkhsPWW78x6s1BWQlmuCfLQrkze",
        "auth0_audience": "https://vinfast-eu-prod.eu.auth0.com/api/v2/",
        "api_base": "https://mobile.connected-car.vinfastauto.eu",
    },
    REGION_VN: {
        "name": "Vietnam",
        "auth0_domain": "vin3s.au.auth0.com",
        "auth0_client_id": "jE5xt50qC7oIh1f32qMzA6hGznIU5mgH",
        "auth0_audience": "https://vin3s.au.auth0.com/api/v2/",
        "api_base": "https://mobile.connected-car.vinfast.vn",
    },
}

# Default region
DEFAULT_REGION = REGION_US

# Legacy API Configuration (for backward compatibility)
AUTH0_DOMAIN = REGIONS[REGION_US]["auth0_domain"]
AUTH0_CLIENT_ID = REGIONS[REGION_US]["auth0_client_id"]
AUTH0_AUDIENCE = REGIONS[REGION_US]["auth0_audience"]
API_BASE = REGIONS[REGION_US]["api_base"]

# Config keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Options keys
CONF_UPDATE_INTERVAL = "update_interval"

# Update intervals (seconds)
# Default: 2.5 hours = ~10 polls per day (respectful of VinFast servers)
UPDATE_INTERVAL_NORMAL = 9000  # 2.5 hours when idle (default) = ~10 polls/day

# Update interval options (in hours for normal)
UPDATE_INTERVAL_OPTIONS = {
    "1 hour (~24/day)": 3600,
    "2 hours (~12/day)": 7200,
    "2.5 hours (~10/day, recommended)": 9000,
    "4 hours (~6/day)": 14400,
    "6 hours (~4/day)": 21600,
    "8 hours (~3/day)": 28800,
    "12 hours (~2/day)": 43200,
}

# Legacy - for backward compatibility
UPDATE_INTERVAL = UPDATE_INTERVAL_NORMAL

# Sensor types
SENSOR_ODOMETER = "odometer"
SENSOR_BATTERY = "battery"
SENSOR_CHARGING = "charging"
SENSOR_RANGE = "range"
