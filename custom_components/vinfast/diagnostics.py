"""Diagnostics support for VinFast integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import VinFastDataUpdateCoordinator

TO_REDACT = {
    CONF_EMAIL,
    CONF_PASSWORD,
    "vinCode",
    "vin",
    "userId",
    "playerId",
    "latitude",
    "longitude",
    "pairing_keys",
    "access_token",
    "refresh_token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: VinFastDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "vin": "**REDACTED**" if coordinator.vin else None,
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "data": async_redact_data(coordinator.data, TO_REDACT) if coordinator.data else None,
    }

    return diagnostics_data
