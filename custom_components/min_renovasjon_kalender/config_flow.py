"""Config flow for Min Renovasjon Kalender."""
from __future__ import annotations

import logging
import re
from typing import Any

import homeassistant.helpers.config_validation as cv
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
    CONF_CALENDAR_DAYS_BACK,
    CONF_COUNTY_ID,
    CONF_EXCLUDED_FRACTION_IDS,
    CONF_HOUSE_NO,
    CONF_STREET_CODE,
    CONF_STREET_NAME,
    DEFAULT_CALENDAR_DAYS,
    DEFAULT_CALENDAR_DAYS_BACK,
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
        """Manage all options: days forward, days back, excluded fractions."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_days = self.config_entry.options.get(
            CONF_CALENDAR_DAYS, DEFAULT_CALENDAR_DAYS
        )
        current_days_back = self.config_entry.options.get(
            CONF_CALENDAR_DAYS_BACK, DEFAULT_CALENDAR_DAYS_BACK
        )
        current_excluded = self.config_entry.options.get(
            CONF_EXCLUDED_FRACTION_IDS, []
        )

        # Fetch available fractions from the API to build the multi-select
        available_fractions = await self._async_get_available_fractions()

        schema_fields: dict[Any, Any] = {
            vol.Optional(
                CONF_CALENDAR_DAYS, default=current_days
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=730)),
            vol.Optional(
                CONF_CALENDAR_DAYS_BACK, default=current_days_back
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=365)),
        }

        if available_fractions:
            schema_fields[
                vol.Optional(
                    CONF_EXCLUDED_FRACTION_IDS, default=current_excluded
                )
            ] = cv.multi_select(available_fractions)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
        )

    async def _async_get_available_fractions(self) -> dict[str, str]:
        """Fetch fractions from API and return {id_str: name} for fractions with data."""
        session = async_get_clientsession(self.hass)
        client = MinRenovasjonApiClient(session)

        county_id = self.config_entry.data.get(CONF_COUNTY_ID, "")
        street_name = self.config_entry.data.get(CONF_STREET_NAME, "")
        street_code = self.config_entry.data.get(CONF_STREET_CODE, "")
        house_no = self.config_entry.data.get(CONF_HOUSE_NO, "")

        try:
            fraksjoner = await client.async_get_fraksjoner(county_id)
            # Fetch a short calendar to see which fractions actually have data
            from datetime import date, timedelta
            import urllib.parse

            fra_dato = date.today().strftime("%Y-%m-%d")
            til_dato = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            encoded_street = urllib.parse.quote(
                urllib.parse.unquote(street_name)
            )
            tommekalender = await client.async_get_tommekalender(
                county_id, encoded_street, street_code, house_no,
                fra_dato, til_dato,
            )
        except MinRenovasjonApiError:
            _LOGGER.warning("Could not fetch fractions for options flow")
            return {}

        if not fraksjoner:
            return {}

        # Build set of fraction IDs that actually appear in the calendar
        active_ids: set[int] = set()
        if tommekalender:
            for entry in tommekalender:
                active_ids.add(int(entry["FraksjonId"]))

        # Return only fractions that have calendar entries (sorted by name)
        fractions: dict[str, str] = {}
        for frac in sorted(fraksjoner, key=lambda f: f["Navn"]):
            fid = int(frac["Id"])
            if not active_ids or fid in active_ids:
                fractions[str(fid)] = frac["Navn"]

        return fractions
