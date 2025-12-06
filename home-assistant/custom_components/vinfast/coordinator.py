"""Data update coordinator for VinFast."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VinFastApi, VinFastApiError, VinFastAuthError
from .const import (
    DOMAIN,
    UPDATE_INTERVAL_NORMAL,
    UPDATE_INTERVAL_CHARGING,
    CONF_OCPP_ENTITY,
    CONF_OCPP_CHARGING_STATE,
    CONF_UPDATE_INTERVAL,
    CONF_CHARGING_UPDATE_INTERVAL,
    CONF_REGION,
    DEFAULT_OCPP_CHARGER_ENTITY,
    DEFAULT_OCPP_CHARGING_STATE,
    DEFAULT_REGION,
)

_LOGGER = logging.getLogger(__name__)


class VinFastDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching VinFast data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        # Get configured update interval or use default
        configured_interval = entry.options.get(CONF_UPDATE_INTERVAL, UPDATE_INTERVAL_NORMAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=configured_interval),
        )
        self.config_entry = entry
        self._api: VinFastApi | None = None
        self._is_ocpp_charging: bool = False
        self._unsub_charger_listener: callable | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from VinFast API."""
        if self._api is None:
            session = async_get_clientsession(self.hass)
            region = self.config_entry.data.get(CONF_REGION, DEFAULT_REGION)
            self._api = VinFastApi(session, region=region)

            # Authenticate
            try:
                await self._api.authenticate(
                    self.config_entry.data[CONF_EMAIL],
                    self.config_entry.data[CONF_PASSWORD],
                )
            except VinFastAuthError as err:
                raise UpdateFailed(f"Authentication failed: {err}") from err
            except VinFastApiError as err:
                raise UpdateFailed(f"API error: {err}") from err

        try:
            return await self._api.get_all_data()
        except VinFastAuthError:
            # Re-authenticate
            try:
                await self._api.authenticate(
                    self.config_entry.data[CONF_EMAIL],
                    self.config_entry.data[CONF_PASSWORD],
                )
                return await self._api.get_all_data()
            except Exception as err:
                raise UpdateFailed(f"Re-authentication failed: {err}") from err
        except VinFastApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    @property
    def vin(self) -> str | None:
        """Return the VIN."""
        if self._api:
            return self._api.vin
        return None

    def _get_ocpp_entity(self) -> str:
        """Get the configured OCPP entity."""
        return self.config_entry.options.get(
            CONF_OCPP_ENTITY, DEFAULT_OCPP_CHARGER_ENTITY
        )

    def _get_ocpp_charging_state(self) -> str:
        """Get the configured OCPP charging state."""
        return self.config_entry.options.get(
            CONF_OCPP_CHARGING_STATE, DEFAULT_OCPP_CHARGING_STATE
        )

    async def async_setup_charger_listener(self) -> None:
        """Set up listener for OCPP charger state changes."""
        ocpp_entity = self._get_ocpp_entity()

        # Skip if no entity configured
        if not ocpp_entity:
            _LOGGER.debug("No OCPP entity configured, skipping charger listener")
            return

        ocpp_charging_state = self._get_ocpp_charging_state()

        # Check initial state
        charger_state = self.hass.states.get(ocpp_entity)
        if charger_state:
            self._is_ocpp_charging = charger_state.state == ocpp_charging_state
            self._update_polling_interval()
            _LOGGER.debug(
                "Initial OCPP charger state: %s (charging=%s)",
                charger_state.state,
                self._is_ocpp_charging,
            )

        # Subscribe to state changes
        self._unsub_charger_listener = async_track_state_change_event(
            self.hass,
            [ocpp_entity],
            self._handle_charger_state_change,
        )
        _LOGGER.debug("Listening for OCPP charger state changes on %s", ocpp_entity)

    @callback
    def _handle_charger_state_change(self, event) -> None:
        """Handle OCPP charger state change."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        was_charging = self._is_ocpp_charging
        ocpp_charging_state = self._get_ocpp_charging_state()
        self._is_ocpp_charging = new_state.state == ocpp_charging_state

        if was_charging != self._is_ocpp_charging:
            _LOGGER.debug(
                "OCPP charger state changed: %s -> %s (charging=%s)",
                event.data.get("old_state", {}).state if event.data.get("old_state") else "unknown",
                new_state.state,
                self._is_ocpp_charging,
            )
            self._update_polling_interval()

            # If charging started, trigger an immediate refresh
            if self._is_ocpp_charging:
                self.hass.async_create_task(self.async_request_refresh())

    def _get_normal_interval(self) -> int:
        """Get configured normal update interval."""
        return self.config_entry.options.get(CONF_UPDATE_INTERVAL, UPDATE_INTERVAL_NORMAL)

    def _get_charging_interval(self) -> int:
        """Get configured charging update interval."""
        return self.config_entry.options.get(CONF_CHARGING_UPDATE_INTERVAL, UPDATE_INTERVAL_CHARGING)

    def _update_polling_interval(self) -> None:
        """Update the polling interval based on charging state."""
        if self._is_ocpp_charging:
            interval_seconds = self._get_charging_interval()
            new_interval = timedelta(seconds=interval_seconds)
            _LOGGER.debug("OCPP charging detected - switching to %d-second polling", interval_seconds)
        else:
            interval_seconds = self._get_normal_interval()
            new_interval = timedelta(seconds=interval_seconds)
            _LOGGER.debug("Not charging - switching to %d-second polling", interval_seconds)

        if self.update_interval != new_interval:
            self.update_interval = new_interval

    def async_unsubscribe(self) -> None:
        """Unsubscribe from charger state changes."""
        if self._unsub_charger_listener:
            self._unsub_charger_listener()
            self._unsub_charger_listener = None
