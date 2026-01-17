"""Sensor platform for VinFast integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VinFastDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VinFastSensorEntityDescription(SensorEntityDescription):
    """Describes VinFast sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any] = lambda x: None


def get_vehicle_value(data: dict[str, Any], key: str) -> Any:
    """Get a value from vehicle data."""
    vehicles = data.get("vehicles", [])
    if vehicles:
        return vehicles[0].get(key)
    return None


def get_odometer_miles(data: dict[str, Any]) -> float | None:
    """Get odometer from telemetry (preferred) or vehicle info (fallback).

    The real-time odometer comes from VEHICLE_STATUS_ODOMETER telemetry alias.
    Falls back to vehicle-info endpoint which may have stale data.
    API returns values in kilometers - we convert to miles.
    """
    KM_TO_MILES = 0.621371

    # First, try the real-time odometer from telemetry (VEHICLE_STATUS_ODOMETER alias)
    odometer_value = get_telemetry_value(data, "odometer")
    if odometer_value is not None:
        try:
            val_km = float(odometer_value)
            _LOGGER.debug("Telemetry odometer (km): %s", val_km)
            # Convert km to miles
            if val_km > 0:
                val_miles = val_km * KM_TO_MILES
                _LOGGER.debug("Telemetry odometer (miles): %s", val_miles)
                return round(val_miles, 1)
        except (ValueError, TypeError):
            pass

    # Fallback to vehicle info (may be stale/cached) - also in km
    value = get_vehicle_value(data, "odometer")
    if value is not None:
        try:
            val_km = float(value)
            _LOGGER.debug("Vehicle info odometer (km, fallback): %s", val_km)
            # Convert km to miles
            val_miles = val_km * KM_TO_MILES
            _LOGGER.debug("Vehicle info odometer (miles): %s", val_miles)
            return round(val_miles, 1)
        except (ValueError, TypeError):
            return None
    return None


def get_telemetry_value(data: dict[str, Any], key: str) -> Any:
    """Get a value from telemetry data."""
    telemetry = data.get("telemetry")
    if telemetry and isinstance(telemetry, dict):
        return telemetry.get(key)
    return None


# Unit conversion constants
KM_TO_MILES = 0.621371
KPA_TO_PSI = 0.145038


def get_range_miles(data: dict[str, Any]) -> float | None:
    """Convert range from km to miles."""
    value = get_telemetry_value(data, "range")
    if value is not None:
        try:
            return round(float(value) * KM_TO_MILES, 1)
        except (ValueError, TypeError):
            pass
    return None


def get_speed_mph(data: dict[str, Any]) -> float | None:
    """Convert speed from km/h to mph."""
    value = get_telemetry_value(data, "speed")
    if value is not None:
        try:
            return round(float(value) * KM_TO_MILES, 1)
        except (ValueError, TypeError):
            pass
    return None


def get_tire_pressure_psi(data: dict[str, Any], key: str) -> float | None:
    """Convert tire pressure from kPa to PSI."""
    value = get_telemetry_value(data, key)
    if value is not None:
        try:
            return round(float(value) * KPA_TO_PSI, 1)
        except (ValueError, TypeError):
            pass
    return None


def get_temperature_f(data: dict[str, Any], key: str) -> float | None:
    """Convert temperature from Celsius to Fahrenheit."""
    value = get_telemetry_value(data, key)
    if value is not None:
        try:
            celsius = float(value)
            return round((celsius * 9 / 5) + 32, 1)
        except (ValueError, TypeError):
            pass
    return None


def get_gear_position(data: dict[str, Any]) -> str | None:
    """Convert gear position number to letter.

    From GearStatus.java in VinFast APK:
    - 0 = OFF (ignition off)
    - 1 = P (Park)
    - 2 = R (Reverse)
    - 3 = N (Neutral)
    - 4 = D (Drive)
    """
    value = get_telemetry_value(data, "gear")
    if value is not None:
        try:
            gear_map = {0: "OFF", 1: "P", 2: "R", 3: "N", 4: "D"}
            return gear_map.get(int(value), str(value))
        except (ValueError, TypeError):
            return str(value)
    return None


def get_charging_status_text(data: dict[str, Any]) -> str | None:
    """Convert charging status code to text."""
    value = get_telemetry_value(data, "charging_status")
    if value is not None:
        try:
            status_map = {
                0: "Not Charging",
                1: "Charging",
                2: "Complete",
                3: "Scheduled",
                4: "Error",
            }
            return status_map.get(int(value), f"Unknown ({value})")
        except (ValueError, TypeError):
            return str(value)
    return None


SENSOR_DESCRIPTIONS: tuple[VinFastSensorEntityDescription, ...] = (
    # ==================== Vehicle Info Sensors ====================
    VinFastSensorEntityDescription(
        key="odometer",
        translation_key="odometer",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        value_fn=lambda data: get_odometer_miles(data),  # API returns km, convert to miles
    ),
    VinFastSensorEntityDescription(
        key="vehicle_name",
        translation_key="vehicle_name",
        icon="mdi:car",
        value_fn=lambda data: get_vehicle_value(data, "customizedVehicleName")
        or get_vehicle_value(data, "vehicleName"),
    ),
    VinFastSensorEntityDescription(
        key="model",
        translation_key="model",
        icon="mdi:car-info",
        value_fn=lambda data: f"{get_vehicle_value(data, 'vehicleType')} {get_vehicle_value(data, 'vehicleVariant')}".strip(),
    ),
    VinFastSensorEntityDescription(
        key="year",
        translation_key="year",
        icon="mdi:calendar",
        value_fn=lambda data: get_vehicle_value(data, "yearOfProduct"),
    ),
    VinFastSensorEntityDescription(
        key="color",
        translation_key="color",
        icon="mdi:palette",
        value_fn=lambda data: get_vehicle_value(data, "exteriorColor"),
    ),
    VinFastSensorEntityDescription(
        key="vin",
        translation_key="vin",
        icon="mdi:identifier",
        value_fn=lambda data: get_vehicle_value(data, "vinCode"),
    ),
    # ==================== Battery & Charging Sensors ====================
    VinFastSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        value_fn=lambda data: get_telemetry_value(data, "battery_level"),
    ),
    VinFastSensorEntityDescription(
        key="battery_12v",
        translation_key="battery_12v",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-battery",
        value_fn=lambda data: get_telemetry_value(data, "lv_battery_level"),
    ),
    VinFastSensorEntityDescription(
        key="range",
        translation_key="range",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: get_range_miles(data),  # API returns km, convert to miles
    ),
    VinFastSensorEntityDescription(
        key="time_to_full",
        translation_key="time_to_full",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer",
        value_fn=lambda data: get_telemetry_value(data, "time_to_full"),
    ),
    VinFastSensorEntityDescription(
        key="charging_status",
        translation_key="charging_status",
        icon="mdi:ev-station",
        value_fn=lambda data: get_charging_status_text(data),
    ),
    VinFastSensorEntityDescription(
        key="charge_limit",
        translation_key="charge_limit",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-charging-high",
        value_fn=lambda data: get_telemetry_value(data, "charge_limit"),
    ),
    # ==================== Speed & Driving Sensors ====================
    VinFastSensorEntityDescription(
        key="speed",
        translation_key="speed",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        value_fn=lambda data: get_speed_mph(data),  # API returns km/h, convert to mph
    ),
    VinFastSensorEntityDescription(
        key="gear",
        translation_key="gear",
        icon="mdi:car-shift-pattern",
        value_fn=lambda data: get_gear_position(data),
    ),
    # ==================== Temperature Sensors ====================
    VinFastSensorEntityDescription(
        key="outside_temp",
        translation_key="outside_temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda data: get_temperature_f(data, "outside_temp"),  # API returns C, convert to F
    ),
    VinFastSensorEntityDescription(
        key="inside_temp",
        translation_key="inside_temp",
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda data: get_temperature_f(data, "inside_temp"),  # API returns C, convert to F
    ),
    # ==================== Tire Pressure Sensors (kPa -> PSI) ====================
    VinFastSensorEntityDescription(
        key="tire_pressure_fl",
        translation_key="tire_pressure_fl",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: get_tire_pressure_psi(data, "tire_pressure_fl"),  # API returns kPa
    ),
    VinFastSensorEntityDescription(
        key="tire_pressure_fr",
        translation_key="tire_pressure_fr",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: get_tire_pressure_psi(data, "tire_pressure_fr"),  # API returns kPa
    ),
    VinFastSensorEntityDescription(
        key="tire_pressure_rl",
        translation_key="tire_pressure_rl",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: get_tire_pressure_psi(data, "tire_pressure_rl"),  # API returns kPa
    ),
    VinFastSensorEntityDescription(
        key="tire_pressure_rr",
        translation_key="tire_pressure_rr",
        native_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: get_tire_pressure_psi(data, "tire_pressure_rr"),  # API returns kPa
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VinFast sensors based on a config entry."""
    coordinator: VinFastDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[VinFastSensor] = []

    # Add predefined sensors
    for description in SENSOR_DESCRIPTIONS:
        entities.append(VinFastSensor(coordinator, description))

    async_add_entities(entities)


class VinFastSensor(CoordinatorEntity[VinFastDataUpdateCoordinator], SensorEntity):
    """Representation of a VinFast sensor."""

    entity_description: VinFastSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VinFastDataUpdateCoordinator,
        description: VinFastSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        # Telemetry-only sensors are only available when we have telemetry data
        # Note: odometer is NOT in this list since it falls back to vehicle info
        telemetry_only_sensors = (
            "battery_level", "battery_12v", "range", "time_to_full",
            "charging_status", "charge_limit", "speed", "gear",
            "outside_temp", "inside_temp", "tire_pressure_fl", "tire_pressure_fr",
            "tire_pressure_rl", "tire_pressure_rr",
        )
        if self.entity_description.key in telemetry_only_sensors:
            return self.coordinator.data and self.coordinator.data.get("telemetry") is not None
        return True
