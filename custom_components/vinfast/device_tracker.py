"""Device tracker platform for VinFast integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VinFastDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VinFast device tracker based on a config entry."""
    coordinator: VinFastDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([VinFastDeviceTracker(coordinator)])


class VinFastDeviceTracker(CoordinatorEntity[VinFastDataUpdateCoordinator], TrackerEntity):
    """Representation of a VinFast vehicle tracker."""

    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_icon = "mdi:car-connected"

    def __init__(self, coordinator: VinFastDataUpdateCoordinator) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.vin}_location"

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
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if self.coordinator.data:
            telemetry = self.coordinator.data.get("telemetry")
            if telemetry and isinstance(telemetry, dict):
                lat = telemetry.get("latitude")
                if lat is not None:
                    try:
                        return float(lat)
                    except (ValueError, TypeError):
                        pass
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if self.coordinator.data:
            telemetry = self.coordinator.data.get("telemetry")
            if telemetry and isinstance(telemetry, dict):
                lon = telemetry.get("longitude")
                if lon is not None:
                    try:
                        return float(lon)
                    except (ValueError, TypeError):
                        pass
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        # Only available if we have location data
        return self.latitude is not None and self.longitude is not None
