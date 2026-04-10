"""Config flow for Min Renovasjon Kalender."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MinRenovasjonApiClient, MinRenovasjonApiError
from .const import (
    CONF_CALENDAR_DAYS,
    CONF_COUNTY_ID,
    CONF_HOUSE_NO,
    CONF_STREET_CODE,
    CONF_STREET_NAME,
    DEFAULT_CALENDAR_DAYS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required("address"): str}
)


class MinRenovasjonKalenderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Min Renovasjon Kalender."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — address lookup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            error, data, title = await self._async_resolve_address(
                user_input["address"]
            )
            if error:
                errors["base"] = error
            elif data is not None:
                # Prevent duplicate entries for the same address
                await self.async_set_unique_id(
                    f"{data[CONF_COUNTY_ID]}_{data[CONF_STREET_CODE]}_{data[CONF_HOUSE_NO]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_resolve_address(
        self, search_string: str
    ) -> tuple[str | None, dict[str, str] | None, str]:
        """Look up the address and validate the municipality."""
        # Normalise vei/veg variants for the search
        normalised = re.sub(
            r"(.*ve)(i|g)(.*)", r"\1*\3", search_string, flags=re.MULTILINE
        )

        session = async_get_clientsession(self.hass)
        client = MinRenovasjonApiClient(session)

        try:
            data = await client.async_address_lookup(normalised)
        except MinRenovasjonApiError:
            return "cannot_connect", None, ""

        if not data or not data.get("adresser"):
            return "no_address_found", None, ""
        if len(data["adresser"]) > 1:
            return "multiple_addresses_found", None, ""

        addr = data["adresser"][0]
        municipality_code = addr["kommunenummer"]

        try:
            is_customer = await client.async_municipality_is_app_customer(
                municipality_code
            )
        except MinRenovasjonApiError:
            return "cannot_connect", None, ""

        if not is_customer:
            return "municipality_not_customer", None, ""

        entry_data = {
            CONF_STREET_NAME: addr["adressenavn"],
            CONF_STREET_CODE: str(addr["adressekode"]),
            CONF_HOUSE_NO: str(addr["nummer"]),
            CONF_COUNTY_ID: str(municipality_code),
        }
        title = (
            f"{addr['adressenavn']} {addr['nummer']}, "
            f"{addr['postnummer']} {addr['poststed']}"
        )
        return None, entry_data, title

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MinRenovasjonKalenderOptionsFlow:
        """Return the options flow handler."""
        return MinRenovasjonKalenderOptionsFlow()


class MinRenovasjonKalenderOptionsFlow(OptionsFlow):
    """Handle options for Min Renovasjon Kalender."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the calendar_days option."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_days = self.config_entry.options.get(
            CONF_CALENDAR_DAYS, DEFAULT_CALENDAR_DAYS
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CALENDAR_DAYS, default=current_days
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=730)),
                }
            ),
        )
