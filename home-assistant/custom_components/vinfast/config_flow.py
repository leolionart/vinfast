"""Config flow for VinFast integration."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VinFastApi, VinFastAuthError, VinFastApiError
from .const import (
    DOMAIN,
    CONF_OCPP_ENTITY,
    CONF_OCPP_CHARGING_STATE,
    CONF_UPDATE_INTERVAL,
    CONF_CHARGING_UPDATE_INTERVAL,
    CONF_REGION,
    DEFAULT_OCPP_CHARGER_ENTITY,
    DEFAULT_OCPP_CHARGING_STATE,
    DEFAULT_REGION,
    REGIONS,
    UPDATE_INTERVAL_NORMAL,
    UPDATE_INTERVAL_CHARGING,
    UPDATE_INTERVAL_OPTIONS,
    CHARGING_UPDATE_INTERVAL_OPTIONS,
)
from .pairing import VinFastPairing, VinFastPairingError

_LOGGER = logging.getLogger(__name__)

# Build region selector options
REGION_OPTIONS = {key: config["name"] for key, config in REGIONS.items()}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(REGION_OPTIONS),
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

CONF_QR_CODE = "qr_code"
CONF_OTP = "otp"
CONF_PAIRING_KEYS = "pairing_keys"


class VinFastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VinFast."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Test credentials
                session = async_get_clientsession(self.hass)
                region = user_input.get(CONF_REGION, DEFAULT_REGION)
                api = VinFastApi(session, region=region)

                await api.authenticate(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )

                # Get vehicles to verify access and get VIN for unique ID
                vehicles = await api.get_vehicles()

                if not vehicles:
                    errors["base"] = "no_vehicles"
                else:
                    # Use first VIN as unique ID
                    vin = vehicles[0].get("vinCode", "unknown")
                    await self.async_set_unique_id(vin)
                    self._abort_if_unique_id_configured()

                    # Create entry with vehicle name
                    vehicle_name = vehicles[0].get(
                        "customizedVehicleName",
                        vehicles[0].get("vehicleName", "VinFast"),
                    )

                    return self.async_create_entry(
                        title=vehicle_name,
                        data=user_input,
                    )

            except VinFastAuthError:
                errors["base"] = "invalid_auth"
            except VinFastApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> VinFastOptionsFlow:
        """Get the options flow for this handler."""
        return VinFastOptionsFlow(config_entry)


class VinFastOptionsFlow(config_entries.OptionsFlow):
    """Handle VinFast options (including pairing for remote control)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._pairing: VinFastPairing | None = None
        self._qr_params: dict[str, str] = {}
        self._encrypted_csr: str = ""
        self._seed: str = ""
        self._api: VinFastApi | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["configure_polling", "pair_remote", "unpair"],
            description_placeholders={
                "is_paired": "Yes" if self.config_entry.options.get(CONF_PAIRING_KEYS) else "No"
            },
        )

    async def async_step_configure_polling(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure telemetry update intervals."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Save the options
            new_options = dict(self.config_entry.options)

            # Get update interval from selection
            interval_selection = user_input.get(CONF_UPDATE_INTERVAL, "4 hours (recommended)")
            new_options[CONF_UPDATE_INTERVAL] = UPDATE_INTERVAL_OPTIONS.get(
                interval_selection, UPDATE_INTERVAL_NORMAL
            )

            # Get charging interval from selection
            charging_selection = user_input.get(CONF_CHARGING_UPDATE_INTERVAL, "5 minutes (recommended)")
            new_options[CONF_CHARGING_UPDATE_INTERVAL] = CHARGING_UPDATE_INTERVAL_OPTIONS.get(
                charging_selection, UPDATE_INTERVAL_CHARGING
            )

            # OCPP entity (optional)
            new_options[CONF_OCPP_ENTITY] = user_input.get(CONF_OCPP_ENTITY, "")
            new_options[CONF_OCPP_CHARGING_STATE] = user_input.get(
                CONF_OCPP_CHARGING_STATE, DEFAULT_OCPP_CHARGING_STATE
            )
            return self.async_create_entry(title="", data=new_options)

        # Get current values
        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, UPDATE_INTERVAL_NORMAL
        )
        current_charging_interval = self.config_entry.options.get(
            CONF_CHARGING_UPDATE_INTERVAL, UPDATE_INTERVAL_CHARGING
        )
        current_entity = self.config_entry.options.get(
            CONF_OCPP_ENTITY, ""
        )
        current_state = self.config_entry.options.get(
            CONF_OCPP_CHARGING_STATE, DEFAULT_OCPP_CHARGING_STATE
        )

        # Find the label for current interval value
        default_interval = "4 hours (recommended)"
        for label, value in UPDATE_INTERVAL_OPTIONS.items():
            if value == current_interval:
                default_interval = label
                break

        default_charging_interval = "5 minutes (recommended)"
        for label, value in CHARGING_UPDATE_INTERVAL_OPTIONS.items():
            if value == current_charging_interval:
                default_charging_interval = label
                break

        return self.async_show_form(
            step_id="configure_polling",
            data_schema=vol.Schema({
                vol.Required(CONF_UPDATE_INTERVAL, default=default_interval): vol.In(
                    list(UPDATE_INTERVAL_OPTIONS.keys())
                ),
                vol.Required(CONF_CHARGING_UPDATE_INTERVAL, default=default_charging_interval): vol.In(
                    list(CHARGING_UPDATE_INTERVAL_OPTIONS.keys())
                ),
                vol.Optional(CONF_OCPP_ENTITY, default=current_entity): str,
                vol.Optional(CONF_OCPP_CHARGING_STATE, default=current_state): str,
            }),
            errors=errors,
        )

    async def async_step_pair_remote(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Enter QR code from car."""
        errors: dict[str, str] = {}

        if user_input is not None:
            qr_content = user_input.get(CONF_QR_CODE, "")

            try:
                # Initialize pairing handler
                session = async_get_clientsession(self.hass)
                self._pairing = VinFastPairing(session)
                self._api = VinFastApi(session)

                # Authenticate
                await self._api.authenticate(
                    self.config_entry.data[CONF_EMAIL],
                    self.config_entry.data[CONF_PASSWORD],
                )
                await self._api.get_vehicles()

                # Parse QR code
                self._qr_params = self._pairing.parse_qr_code(qr_content)

                # Validate VIN matches
                self._pairing.validate_qr_for_vehicle(
                    self._qr_params,
                    self._api.vin or "",
                    self._api.user_id,
                )

                # Generate keypair and CSR
                self._pairing.generate_keypair()
                device_id = str(uuid.uuid4())[:8]
                csr = self._pairing.generate_csr(
                    self._api.vin or "",
                    device_id,
                    "HomeAssistant"
                )

                # Encrypt CSR
                self._encrypted_csr, self._seed = self._pairing.encrypt_csr(
                    csr,
                    self._qr_params["K"],
                    self._api.vin or "",
                )

                # Trigger OTP
                await self._pairing.verify_session(
                    self._api._access_token or "",
                    self._qr_params["ssid"],
                    email=self.config_entry.data.get(CONF_EMAIL),
                )

                # Move to OTP step
                return await self.async_step_enter_otp()

            except VinFastPairingError as err:
                _LOGGER.error("Pairing error: %s", err)
                errors["base"] = "pairing_failed"
            except VinFastAuthError:
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.exception("Unexpected pairing error: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="pair_remote",
            data_schema=vol.Schema({
                vol.Required(CONF_QR_CODE): str,
            }),
            errors=errors,
            description_placeholders={
                "instructions": "Go to your VinFast vehicle, open Settings > Remote Control > Pair New Device. Enter the QR code content shown on the screen."
            },
        )

    async def async_step_enter_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Enter OTP received via email/phone."""
        errors: dict[str, str] = {}

        if user_input is not None:
            otp = user_input.get(CONF_OTP, "")

            try:
                if not self._pairing or not self._api:
                    raise VinFastPairingError("Pairing session lost")

                # Send pairing data with OTP
                response = await self._pairing.send_pair_data(
                    self._api._access_token or "",
                    self._encrypted_csr,
                    otp,
                    self._seed,
                    self._qr_params["ssid"],
                    email=self.config_entry.data.get(CONF_EMAIL),
                )

                # Store keys in options
                keys = self._pairing.export_keys()

                return self.async_create_entry(
                    title="",
                    data={CONF_PAIRING_KEYS: keys},
                )

            except VinFastPairingError as err:
                _LOGGER.error("OTP verification failed: %s", err)
                errors["base"] = "invalid_otp"
            except Exception as err:
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="enter_otp",
            data_schema=vol.Schema({
                vol.Required(CONF_OTP): str,
            }),
            errors=errors,
            description_placeholders={
                "instructions": "Enter the OTP code sent to your email or phone."
            },
        )

    async def async_step_unpair(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove pairing keys."""
        if user_input is not None:
            # Clear pairing keys
            return self.async_create_entry(
                title="",
                data={CONF_PAIRING_KEYS: None},
            )

        return self.async_show_form(
            step_id="unpair",
            description_placeholders={
                "warning": "This will remove the remote control pairing. You'll need to re-pair at your vehicle to use remote commands again."
            },
        )
