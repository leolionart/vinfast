"""Data update coordinator for VinFast."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VinFastApi, VinFastApiError, VinFastAuthError
from .const import (
    DOMAIN,
    UPDATE_INTERVAL_NORMAL,
    CONF_UPDATE_INTERVAL,
    CONF_REGION,
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
