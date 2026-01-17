"""VinFast Connected Car API Client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

from .const import (
    AUTH0_DOMAIN,
    AUTH0_CLIENT_ID,
    AUTH0_AUDIENCE,
    API_BASE,
    DEFAULT_REGION,
    REGIONS,
)

_LOGGER = logging.getLogger(__name__)

# Request ALL aliases mode - when True, requests all available aliases from server
# This allows discovery of all available data points
# Set to False for normal operation (requests only core aliases)
REQUEST_ALL_ALIASES = False

# Core aliases that we always want (used for friendly name mapping)
# These are the most commonly used data points
CORE_TELEMETRY_ALIASES = [
    # Battery & Charging
    "VEHICLE_STATUS_HV_BATTERY_SOC",          # Battery state of charge (%)
    "VEHICLE_STATUS_LV_BATTERY_SOC",          # 12V/Low voltage battery SOC (%)
    "VEHICLE_STATUS_REMAINING_DISTANCE",      # Estimated range (km)
    "VEHICLE_STATUS_ODOMETER",                # Real-time odometer (km)
    "CHARGING_STATUS_CHARGING_STATUS",        # Charging state (ChargingState enum)
    "CHARGING_STATUS_CHARGING_REMAINING_TIME", # Time to full charge (Long)
    "CHARGE_CONTROL_CURRENT_TARGET_SOC",      # Charge limit/target SOC (%)
    # Vehicle Status
    "VEHICLE_STATUS_IGNITION_STATUS",         # Ignition on/off
    "VEHICLE_STATUS_GEAR_POSITION",           # Gear position (P/R/N/D)
    "VEHICLE_STATUS_VEHICLE_SPEED",           # Speed (km/h)
    "VEHICLE_STATUS_HANDBRAKE_STATUS",        # Handbrake status
    # Climate/Temperature
    "VEHICLE_STATUS_AMBIENT_TEMPERATURE",     # Outside temp (C)
    "CLIMATE_INFORMATION_DRIVER_TEMPERATURE", # Interior/driver temp (C)
    # Tire Pressure
    "VEHICLE_STATUS_FRONT_LEFT_TIRE_PRESSURE",
    "VEHICLE_STATUS_FRONT_RIGHT_TIRE_PRESSURE",
    "VEHICLE_STATUS_REAR_LEFT_TIRE_PRESSURE",
    "VEHICLE_STATUS_REAR_RIGHT_TIRE_PRESSURE",
    # Door Status
    "DOOR_AJAR_FRONT_LEFT_DOOR_STATUS",
    "DOOR_AJAR_FRONT_RIGHT_DOOR_STATUS",
    "DOOR_AJAR_REAR_LEFT_DOOR_STATUS",
    "DOOR_AJAR_REAR_RIGHT_DOOR_STATUS",
    "DOOR_TRUNK_DOOR_STATUS",
    # Remote Control Status
    "REMOTE_CONTROL_DOOR_STATUS",
    "REMOTE_CONTROL_BONNET_CONTROL_STATUS",
    "REMOTE_CONTROL_WINDOW_STATUS",
    "REMOTE_CONTROL_CHARGE_PORT_STATUS",
    # Location
    "LOCATION_LATITUDE",
    "LOCATION_LONGITUDE",
    "VEHICLE_BEARING_DEGREE",
]

# Fallback static resource paths (used if get-alias fails)
# These paths are based on LwM2M Object IDs observed in the VinFast app
FALLBACK_TELEMETRY_RESOURCES = [
    "/34196/0/0",   # Battery level (%)
    "/34196/0/1",   # Range estimate
    "/34197/0/0",   # Charging status
    "/34197/0/1",   # Charging power (kW)
    "/34197/0/2",   # Time to full charge
    "/34193/0/0",   # Charge limit (%)
    "/34200/0/0",   # Vehicle latitude
    "/34200/0/1",   # Vehicle longitude
    "/34201/0/0",   # Lock status
    "/34202/0/0",   # Climate status
    # Try additional paths that might have odometer
    # VinFast uses custom LwM2M objects in the 34xxx range
    "/34189/0/0",   # Try various object IDs
    "/34190/0/0",
    "/34191/0/0",
    "/34192/0/0",
    "/34194/0/0",
    "/34195/0/0",
    "/34198/0/0",
    "/34199/0/0",
    "/34203/0/0",
    "/34204/0/0",
    "/34205/0/0",
    "/34206/0/0",
    "/34207/0/0",
    "/34208/0/0",
    "/34209/0/0",
    "/34210/0/0",
]


class VinFastApiError(Exception):
    """Exception for VinFast API errors."""


class VinFastAuthError(VinFastApiError):
    """Exception for authentication errors."""


class VinFastApi:
    """VinFast Connected Car API Client."""

    def __init__(self, session: aiohttp.ClientSession, region: str = DEFAULT_REGION) -> None:
        """Initialize the API client."""
        self._session = session
        self._region = region
        self._region_config = REGIONS.get(region, REGIONS[DEFAULT_REGION])
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._user_id: str | None = None
        self._vin: str | None = None
        self._alias_mappings: dict[str, dict[str, str]] = {}  # alias -> {path, objectId, etc}
        self._alias_version: str | None = None

    @property
    def auth0_domain(self) -> str:
        """Return Auth0 domain for current region."""
        return self._region_config["auth0_domain"]

    @property
    def auth0_client_id(self) -> str:
        """Return Auth0 client ID for current region."""
        return self._region_config["auth0_client_id"]

    @property
    def auth0_audience(self) -> str:
        """Return Auth0 audience for current region."""
        return self._region_config["auth0_audience"]

    @property
    def api_base(self) -> str:
        """Return API base URL for current region."""
        return self._region_config["api_base"]

    @property
    def vin(self) -> str | None:
        """Return the VIN."""
        return self._vin

    @property
    def user_id(self) -> str | None:
        """Return the user ID."""
        return self._user_id

    async def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with VinFast Connected Car services."""
        url = f"https://{self.auth0_domain}/oauth/token"

        payload = {
            "client_id": self.auth0_client_id,
            "audience": self.auth0_audience,
            "grant_type": "password",
            "scope": "offline_access openid profile email",
            "username": email,
            "password": password,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with async_timeout.timeout(30):
                async with self._session.post(
                    url, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._access_token = data["access_token"]
                        self._refresh_token = data.get("refresh_token")
                        _LOGGER.debug("Authentication successful")
                        return True
                    elif response.status == 401:
                        raise VinFastAuthError("Invalid credentials")
                    else:
                        text = await response.text()
                        _LOGGER.error("Auth failed: %s - %s", response.status, text)
                        raise VinFastApiError(f"Authentication failed: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during auth: %s", err)
            raise VinFastApiError(f"Connection error: {err}") from err

    async def refresh_auth(self) -> bool:
        """Refresh the access token."""
        if not self._refresh_token:
            return False

        url = f"https://{self.auth0_domain}/oauth/token"

        payload = {
            "client_id": self.auth0_client_id,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        try:
            async with async_timeout.timeout(30):
                async with self._session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._access_token = data["access_token"]
                        self._refresh_token = data.get("refresh_token", self._refresh_token)
                        return True
                    return False
        except Exception as err:
            _LOGGER.error("Token refresh failed: %s", err)
            return False

    def _get_headers(self) -> dict[str, str]:
        """Build headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-service-name": "CAPP",
            "x-app-version": "1.10.3",
            "x-device-platform": "HomeAssistant",
            "x-device-family": "Integration",
            "x-device-os-version": "1.0",
            "x-device-locale": "en-US",
            "x-timezone": "America/New_York",
            "x-device-identifier": "ha-vinfast-integration",
        }
        if self._vin:
            headers["x-vin-code"] = self._vin
        if self._user_id:
            headers["x-player-identifier"] = self._user_id
        return headers

    async def _api_request(
        self, method: str, endpoint: str, data: dict | None = None
    ) -> dict[str, Any]:
        """Make an API request."""
        url = f"{self.api_base}{endpoint}"

        try:
            async with async_timeout.timeout(30):
                if method == "GET":
                    async with self._session.get(
                        url, headers=self._get_headers()
                    ) as response:
                        return await self._handle_response(response)
                elif method == "POST":
                    async with self._session.post(
                        url, headers=self._get_headers(), json=data
                    ) as response:
                        return await self._handle_response(response)
        except aiohttp.ClientError as err:
            _LOGGER.error("API request failed: %s", err)
            raise VinFastApiError(f"API request failed: {err}") from err

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle API response."""
        if response.status == 401:
            if await self.refresh_auth():
                raise VinFastApiError("Token refreshed, retry request")
            raise VinFastAuthError("Authentication expired")

        if response.status != 200:
            text = await response.text()
            raise VinFastApiError(f"API error {response.status}: {text}")

        data = await response.json()
        if data.get("code") not in (0, 200000):
            raise VinFastApiError(f"API error: {data.get('message', 'Unknown error')}")

        return data

    async def get_vehicles(self) -> list[dict[str, Any]]:
        """Get list of vehicles for the account."""
        data = await self._api_request("GET", "/ccarusermgnt/api/v1/user-vehicle")
        vehicles = data.get("data", [])

        if vehicles:
            self._vin = vehicles[0].get("vinCode")
            self._user_id = vehicles[0].get("userId")

        return vehicles

    async def get_alias_mappings(self, version: str = "1.0") -> dict[str, dict[str, str]]:
        """Fetch alias-to-resource-path mappings from the server.

        This retrieves the dynamic mapping between human-readable aliases
        (like VEHICLE_STATUS_ODOMETER) and LwM2M resource paths (like /34xxx/0/0).
        """
        if self._alias_mappings and self._alias_version == version:
            return self._alias_mappings

        try:
            # This endpoint may have different response format, so we call it directly
            url = f"{self.api_base}/modelmgmt/api/v2/vehicle-model/mobile-app/vehicle/get-alias?version={version}"

            async with async_timeout.timeout(30):
                async with self._session.get(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        _LOGGER.warning("get-alias returned status %s", response.status)
                        return {}

                    data = await response.json()
                    _LOGGER.debug("get-alias response: %s", data)

            # Parse the response - handle different possible formats
            resources = []
            if isinstance(data, dict):
                # Try: {"data": {"resources": [...]}}
                resources = data.get("data", {}).get("resources", [])
                # Try: {"data": [...]}
                if not resources and isinstance(data.get("data"), list):
                    resources = data.get("data", [])
                # Try: {"resources": [...]}
                if not resources:
                    resources = data.get("resources", [])
            elif isinstance(data, list):
                resources = data

            mappings = {}
            for resource in resources:
                alias = resource.get("alias")
                if alias:
                    obj_id = resource.get("devObjID", "")
                    inst_id = resource.get("devObjInstID", "0")
                    rsrc_id = resource.get("devRsrcID", "0")

                    # Build the resource path: /{objectId}/{instanceId}/{resourceId}
                    path = f"/{obj_id}/{inst_id}/{rsrc_id}"

                    mappings[alias] = {
                        "path": path,
                        "objectId": obj_id,
                        "instanceId": inst_id,
                        "resourceId": rsrc_id,
                        "name": resource.get("name", ""),
                        "units": resource.get("units", ""),
                        "type": resource.get("type", ""),
                    }

            if mappings:
                self._alias_mappings = mappings
                self._alias_version = version
                _LOGGER.debug("Loaded %d alias mappings from server", len(mappings))

                # Log which of our requested aliases were found
                found = [a for a in CORE_TELEMETRY_ALIASES if a in mappings]
                missing = [a for a in CORE_TELEMETRY_ALIASES if a not in mappings]
                _LOGGER.debug("Aliases found: %d, missing: %d", len(found), len(missing))

            return mappings

        except (aiohttp.ClientError, Exception) as err:
            _LOGGER.warning("Failed to fetch alias mappings: %s", err)
            return {}

    async def get_profile(self) -> dict[str, Any]:
        """Get user profile."""
        data = await self._api_request(
            "GET", "/ccarusermgnt/api/v1/auth0/account/profile"
        )
        return data.get("data", {})

    async def get_telemetry(self) -> dict[str, Any] | None:
        """Get vehicle telemetry data.

        When REQUEST_ALL_ALIASES is True, requests ALL available aliases from the server.
        This enables discovery of all data points the vehicle provides.
        """
        if not self._vin:
            _LOGGER.info("TELEMETRY: No VIN available, skipping telemetry fetch")
            return None

        # Try to fetch alias mappings first (for dynamic resource paths)
        alias_mappings = await self.get_alias_mappings()
        _LOGGER.debug("Telemetry: alias_mappings returned %d mappings", len(alias_mappings) if alias_mappings else 0)

        # Build request objects from alias mappings
        # API expects: [{"instanceId": "1", "objectId": "34183", "resourceId": "3"}, ...]
        request_objects = []
        path_to_alias = {}  # Reverse mapping for parsing response

        if alias_mappings:
            if REQUEST_ALL_ALIASES:
                # Request ALL available aliases for comprehensive data discovery
                for alias, mapping in alias_mappings.items():
                    path = mapping["path"]
                    request_objects.append({
                        "objectId": mapping["objectId"],
                        "instanceId": mapping["instanceId"],
                        "resourceId": mapping["resourceId"],
                    })
                    path_to_alias[path] = alias
                _LOGGER.info("Telemetry: Requesting ALL %d aliases for comprehensive data", len(request_objects))
            else:
                # Use only core aliases
                for alias in CORE_TELEMETRY_ALIASES:
                    if alias in alias_mappings:
                        mapping = alias_mappings[alias]
                        path = mapping["path"]
                        request_objects.append({
                            "objectId": mapping["objectId"],
                            "instanceId": mapping["instanceId"],
                            "resourceId": mapping["resourceId"],
                        })
                        path_to_alias[path] = alias
                _LOGGER.debug("Telemetry: Using %d core resources", len(request_objects))
        else:
            # Fallback to static paths - parse them into object format
            for path in FALLBACK_TELEMETRY_RESOURCES:
                parts = path.strip("/").split("/")
                if len(parts) == 3:
                    request_objects.append({
                        "objectId": parts[0],
                        "instanceId": parts[1],
                        "resourceId": parts[2],
                    })
            _LOGGER.debug("Telemetry: Using %d fallback static resources", len(request_objects))

        if not request_objects:
            _LOGGER.warning("No telemetry resource paths available")
            return None

        _LOGGER.debug("Telemetry: Requesting %d resources", len(request_objects))

        try:
            # Use the "ping" endpoint which returns cached telemetry data
            # This works even when the vehicle is asleep
            data = await self._api_request(
                "POST",
                "/ccaraccessmgmt/api/v1/telemetry/app/ping",
                request_objects,  # Send array directly, not wrapped in object
            )
            raw_data = data.get("data")
            if not raw_data:
                _LOGGER.debug("Telemetry: No data in response")
                return None

            _LOGGER.info("Telemetry: Received %d values out of %d requested",
                        len(raw_data) if isinstance(raw_data, list) else 0,
                        len(request_objects))

            # Parse ping response - it's a list of VehiclePingResourceDto objects
            return self._parse_ping_response(raw_data, path_to_alias, alias_mappings)
        except VinFastApiError as err:
            _LOGGER.debug("Telemetry request failed: %s", err)
            return None

    def _parse_ping_response(
        self, raw_data: list, path_to_alias: dict[str, str] | None = None,
        alias_mappings: dict[str, dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """Parse ping response into friendly format.

        Ping response is a list of objects like:
        {
            "resourceId": 3,
            "instanceId": 1,
            "objectId": 34183,
            "deviceKey": "34183_00001_00003",
            "value": "13059.5",
            "lastUpdateTime": "2024-..."
        }

        deviceKey format is: {objectId}_{instanceId:05d}_{resourceId:05d}
        """
        result = {}
        # Also store raw alias data for comprehensive monitoring
        result["_raw_aliases"] = {}

        if not isinstance(raw_data, list):
            _LOGGER.debug("Telemetry: ping response is not a list: %s", type(raw_data))
            return result

        # Map core aliases to friendly keys for backward compatibility
        alias_to_key = {
            # Battery & Charging
            "VEHICLE_STATUS_HV_BATTERY_SOC": "battery_level",
            "VEHICLE_STATUS_LV_BATTERY_SOC": "lv_battery_level",
            "VEHICLE_STATUS_REMAINING_DISTANCE": "range",
            "VEHICLE_STATUS_ODOMETER": "odometer",
            "CHARGING_STATUS_CHARGING_STATUS": "charging_status",
            "CHARGING_STATUS_CHARGING_REMAINING_TIME": "time_to_full",
            "CHARGE_CONTROL_CURRENT_TARGET_SOC": "charge_limit",
            "CHARGE_CONTROL_SAMPLE_CHARGE_STATUS": "sample_charge_status",
            # Vehicle Status
            "VEHICLE_STATUS_IGNITION_STATUS": "ignition",
            "VEHICLE_STATUS_GEAR_POSITION": "gear",
            "VEHICLE_STATUS_VEHICLE_SPEED": "speed",
            "VEHICLE_STATUS_HANDBRAKE_STATUS": "handbrake",
            # Climate
            "VEHICLE_STATUS_AMBIENT_TEMPERATURE": "outside_temp",
            "CLIMATE_INFORMATION_DRIVER_TEMPERATURE": "inside_temp",
            "CLIMATE_INFORMATION_STATUS": "climate_status",
            # Tire Pressure
            "VEHICLE_STATUS_FRONT_LEFT_TIRE_PRESSURE": "tire_pressure_fl",
            "VEHICLE_STATUS_FRONT_RIGHT_TIRE_PRESSURE": "tire_pressure_fr",
            "VEHICLE_STATUS_REAR_LEFT_TIRE_PRESSURE": "tire_pressure_rl",
            "VEHICLE_STATUS_REAR_RIGHT_TIRE_PRESSURE": "tire_pressure_rr",
            # Door Status
            "DOOR_AJAR_FRONT_LEFT_DOOR_STATUS": "door_fl",
            "DOOR_AJAR_FRONT_RIGHT_DOOR_STATUS": "door_fr",
            "DOOR_AJAR_REAR_LEFT_DOOR_STATUS": "door_rl",
            "DOOR_AJAR_REAR_RIGHT_DOOR_STATUS": "door_rr",
            "DOOR_TRUNK_DOOR_STATUS": "trunk_status",
            # Remote Control Status
            "REMOTE_CONTROL_DOOR_STATUS": "locked",
            "REMOTE_CONTROL_BONNET_CONTROL_STATUS": "hood_status",
            "REMOTE_CONTROL_WINDOW_STATUS": "window_status",
            "REMOTE_CONTROL_CHARGE_PORT_STATUS": "plugged_in",
            # Location
            "LOCATION_LATITUDE": "latitude",
            "LOCATION_LONGITUDE": "longitude",
            "VEHICLE_BEARING_DEGREE": "heading",
        }

        for item in raw_data:
            if not isinstance(item, dict):
                continue

            device_key = item.get("deviceKey")
            value = item.get("value")
            last_update = item.get("lastUpdateTime")

            if device_key and value is not None:

                # Parse deviceKey format: 34183_00001_00003 -> /34183/1/3
                parts = device_key.split("_")
                if len(parts) == 3:
                    obj_id = str(int(parts[0]))  # Remove leading zeros
                    inst_id = str(int(parts[1]))  # Remove leading zeros
                    rsrc_id = str(int(parts[2]))  # Remove leading zeros
                    path = f"/{obj_id}/{inst_id}/{rsrc_id}"
                else:
                    path = device_key

                # Get the alias name for this path
                alias = path_to_alias.get(path, path) if path_to_alias else path

                # Store in raw_aliases for comprehensive monitoring (use alias name as key)
                try:
                    parsed_value = float(value)
                except (ValueError, TypeError):
                    parsed_value = value

                result["_raw_aliases"][alias] = {
                    "value": parsed_value,
                    "path": path,
                    "last_update": last_update,
                }

                # Use alias_to_key for backward-compatible friendly names
                friendly_key = alias_to_key.get(alias, alias.lower())

                # Store in main result with friendly key
                result[friendly_key] = parsed_value

        _LOGGER.debug("Telemetry: Parsed %d values", len(result) - 1)  # -1 for _raw_aliases

        return result

    async def get_locations(self) -> list[dict[str, Any]]:
        """Get saved locations."""
        try:
            data = await self._api_request(
                "GET", "/ccarusermgnt/api/v1/location-favorite"
            )
            return data.get("data", [])
        except VinFastApiError:
            return []

    async def get_all_data(self) -> dict[str, Any]:
        """Get all available vehicle data."""
        result = {
            "vehicles": [],
            "profile": {},
            "telemetry": None,
            "locations": [],
        }

        try:
            result["vehicles"] = await self.get_vehicles()
        except VinFastApiError as err:
            _LOGGER.warning("Failed to get vehicles: %s", err)

        try:
            result["profile"] = await self.get_profile()
        except VinFastApiError as err:
            _LOGGER.warning("Failed to get profile: %s", err)

        try:
            result["telemetry"] = await self.get_telemetry()
        except VinFastApiError as err:
            _LOGGER.debug("Telemetry unavailable: %s", err)

        try:
            result["locations"] = await self.get_locations()
        except VinFastApiError as err:
            _LOGGER.debug("Locations unavailable: %s", err)

        return result
