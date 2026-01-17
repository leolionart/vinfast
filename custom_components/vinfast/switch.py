"""Switch platform for VinFast integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VinFastDataUpdateCoordinator
from .pairing import VinFastPairing, CONTROL_ALIASES

_LOGGER = logging.getLogger(__name__)

CONF_PAIRING_KEYS = "pairing_keys"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VinFast switches based on a config entry."""
    coordinator: VinFastDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Only add climate switch if paired
    pairing_keys = entry.options.get(CONF_PAIRING_KEYS)
    if pairing_keys:
        entities = [VinFastClimateSwitch(coordinator, entry)]
        async_add_entities(entities)
    else:
        _LOGGER.info("Remote control not paired - climate switch not available")


class VinFastClimateSwitch(CoordinatorEntity[VinFastDataUpdateCoordinator], SwitchEntity):
    """Representation of VinFast climate control switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "climate"
    _attr_icon = "mdi:air-conditioner"

    def __init__(
        self,
        coordinator: VinFastDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.vin}_climate"
        self._pairing: VinFastPairing | None = None
        self._is_on: bool = False

        # Try to load pairing keys
        self._load_pairing_keys()

    def _load_pairing_keys(self) -> None:
        """Load pairing keys from config entry options."""
        pairing_keys = self._entry.options.get(CONF_PAIRING_KEYS)
        if pairing_keys:
            from homeassistant.helpers.aiohttp_client import async_get_clientsession
            session = async_get_clientsession(self.coordinator.hass)
            self._pairing = VinFastPairing(session)
            if self._pairing.import_keys(pairing_keys):
                _LOGGER.info("Pairing keys loaded for climate control")
            else:
                _LOGGER.warning("Failed to load pairing keys")
                self._pairing = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this VinFast vehicle."""
        vehicles = self.coordinator.data.get("vehicles", []) if self.coordinator.data else []
        vehicle = vehicles[0] if vehicles else {}

        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.vin or "unknown")},
            name=vehicle.get("customizedVehicleName", vehicle.get("vehicleName", "VinFast")),
            manufacturer="VinFast",
            model=f"{vehicle.get('vehicleType', '')} {vehicle.get('vehicleVariant', '')}".strip(),
            sw_version=str(vehicle.get("yearOfProduct", "")),
        )

    @property
    def is_on(self) -> bool:
        """Return true if climate is on."""
        # Try to get from telemetry if available
        if self.coordinator.data:
            telemetry = self.coordinator.data.get("telemetry", {})
            if telemetry:
                climate_status = telemetry.get("climate_on") or telemetry.get("ac_status")
                if climate_status is not None:
                    try:
                        return int(climate_status) == 1
                    except (ValueError, TypeError):
                        pass
        return self._is_on

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        # Available only if paired
        return self._pairing is not None and self._pairing.is_paired

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on climate control."""
        await self._send_climate_command(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off climate control."""
        await self._send_climate_command(0)

    async def _send_climate_command(self, value: int) -> None:
        """Send climate control command."""
        if not self._pairing or not self._pairing.is_paired:
            _LOGGER.error("Cannot send command - not paired")
            return

        # Re-authenticate to get fresh token
        from homeassistant.helpers.aiohttp_client import async_get_clientsession
        from .api import VinFastApi
        from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

        session = async_get_clientsession(self.coordinator.hass)
        api = VinFastApi(session)

        try:
            await api.authenticate(
                self._entry.data[CONF_EMAIL],
                self._entry.data[CONF_PASSWORD],
            )
            await api.get_vehicles()

            # Get device key for climate control
            device_key = CONTROL_ALIASES.get("CLIMATE_CONTROL_AIR_CONDITION_ENABLE", "3416_0_5850")

            # Send command
            success = await self._pairing.send_command(
                access_token=api._access_token or "",
                message_name="CLIMATE_CONTROL_AIR_CONDITION_ENABLE",
                device_key=device_key,
                value=value,
                user_id=api.user_id or "",
                session_id=self._pairing._session_id or "",
            )

            if success:
                self._is_on = value == 1
                _LOGGER.info("Climate %s command sent successfully", "ON" if value else "OFF")
                # Trigger coordinator refresh after a delay
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to send climate command")

        except Exception as err:
            _LOGGER.exception("Error sending climate command: %s", err)
