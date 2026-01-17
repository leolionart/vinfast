"""Binary sensor platform for VinFast integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VinFastDataUpdateCoordinator


@dataclass(frozen=True)
class VinFastBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes VinFast binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool | None] = lambda x: None


def get_telemetry_value(data: dict[str, Any], key: str) -> Any:
    """Get a value from telemetry data."""
    telemetry = data.get("telemetry")
    if telemetry and isinstance(telemetry, dict):
        return telemetry.get(key)
    return None


def is_locked(data: dict[str, Any]) -> bool | None:
    """Check if vehicle is unlocked for BinarySensorDeviceClass.LOCK.

    VinFast API: 0=unlocked, 1=locked (from DoorsInfo.java)
    Home Assistant LOCK device class: is_on=True means UNLOCKED

    So we return True when value == 0 (unlocked), False when value == 1 (locked).
    """
    value = get_telemetry_value(data, "locked")
    if value is not None:
        try:
            # Return True if unlocked (value==0), False if locked (value==1)
            return int(value) == 0
        except (ValueError, TypeError):
            return None
    return None


def is_ignition_on(data: dict[str, Any]) -> bool | None:
    """Check if ignition is on (0=off, 1=on)."""
    value = get_telemetry_value(data, "ignition")
    if value is not None:
        try:
            return int(value) == 1
        except (ValueError, TypeError):
            return None
    return None


def is_charging(data: dict[str, Any]) -> bool | None:
    """Check if vehicle is charging (1=charging)."""
    value = get_telemetry_value(data, "charging_status")
    if value is not None:
        try:
            return int(value) == 1
        except (ValueError, TypeError):
            return None
    return None


def is_plugged_in(data: dict[str, Any]) -> bool | None:
    """Check if charger is plugged in."""
    # Try the dedicated charge port status first
    value = get_telemetry_value(data, "plugged_in")
    if value is not None:
        try:
            return int(value) == 1
        except (ValueError, TypeError):
            pass
    # Fallback: plugged in if charging status is not 0
    value = get_telemetry_value(data, "charging_status")
    if value is not None:
        try:
            return int(value) > 0
        except (ValueError, TypeError):
            return None
    return None


def is_trunk_open(data: dict[str, Any]) -> bool | None:
    """Check if trunk is open (0=closed, 1=open)."""
    value = get_telemetry_value(data, "trunk_status")
    if value is not None:
        try:
            return int(value) == 1
        except (ValueError, TypeError):
            return None
    return None


def is_hood_open(data: dict[str, Any]) -> bool | None:
    """Check if hood is open (0=closed, 1=open)."""
    value = get_telemetry_value(data, "hood_status")
    if value is not None:
        try:
            return int(value) == 1
        except (ValueError, TypeError):
            return None
    return None


def is_door_open(data: dict[str, Any], door_key: str) -> bool | None:
    """Check if a specific door is open (DoorStatus enum: 0=closed, 1=open)."""
    value = get_telemetry_value(data, door_key)
    if value is not None:
        try:
            return int(value) == 1
        except (ValueError, TypeError):
            return None
    return None


def is_any_door_open(data: dict[str, Any]) -> bool | None:
    """Check if any door is open (DoorStatus enum: 0=closed, 1=open)."""
    # Check individual door statuses
    door_keys = ["door_fl", "door_fr", "door_rl", "door_rr"]
    any_found = False
    for key in door_keys:
        value = get_telemetry_value(data, key)
        if value is not None:
            any_found = True
            try:
                if int(value) == 1:  # Open
                    return True
            except (ValueError, TypeError):
                pass
    # If we found any door status, return False (all closed), otherwise None
    return False if any_found else None


def is_any_window_open(data: dict[str, Any]) -> bool | None:
    """Check if any window is open."""
    value = get_telemetry_value(data, "window_status")
    if value is not None:
        try:
            # If non-zero, at least one window is open
            return int(value) != 0
        except (ValueError, TypeError):
            return None
    return None


BINARY_SENSOR_DESCRIPTIONS: tuple[VinFastBinarySensorEntityDescription, ...] = (
    VinFastBinarySensorEntityDescription(
        key="locked",
        translation_key="locked",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:car-door-lock",
        value_fn=lambda data: is_locked(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="ignition",
        translation_key="ignition",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:car-key",
        value_fn=lambda data: is_ignition_on(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:ev-station",
        value_fn=lambda data: is_charging(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="plugged_in",
        translation_key="plugged_in",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
        value_fn=lambda data: is_plugged_in(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="trunk_open",
        translation_key="trunk_open",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:car-back",
        value_fn=lambda data: is_trunk_open(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="hood_open",
        translation_key="hood_open",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:car-lifted-pickup",
        value_fn=lambda data: is_hood_open(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="door_open",
        translation_key="door_open",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: is_any_door_open(data),
    ),
    VinFastBinarySensorEntityDescription(
        key="window_open",
        translation_key="window_open",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-door",
        value_fn=lambda data: is_any_window_open(data),
    ),
    # Individual door sensors
    VinFastBinarySensorEntityDescription(
        key="door_front_left",
        translation_key="door_front_left",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: is_door_open(data, "door_fl"),
    ),
    VinFastBinarySensorEntityDescription(
        key="door_front_right",
        translation_key="door_front_right",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: is_door_open(data, "door_fr"),
    ),
    VinFastBinarySensorEntityDescription(
        key="door_rear_left",
        translation_key="door_rear_left",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: is_door_open(data, "door_rl"),
    ),
    VinFastBinarySensorEntityDescription(
        key="door_rear_right",
        translation_key="door_rear_right",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: is_door_open(data, "door_rr"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VinFast binary sensors based on a config entry."""
    coordinator: VinFastDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[VinFastBinarySensor] = []

    for description in BINARY_SENSOR_DESCRIPTIONS:
        entities.append(VinFastBinarySensor(coordinator, description))

    async_add_entities(entities)


class VinFastBinarySensor(CoordinatorEntity[VinFastDataUpdateCoordinator], BinarySensorEntity):
    """Representation of a VinFast binary sensor."""

    entity_description: VinFastBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VinFastDataUpdateCoordinator,
        description: VinFastBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.vin}_{description.key}"

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
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.coordinator.data and self.coordinator.data.get("telemetry") is not None
