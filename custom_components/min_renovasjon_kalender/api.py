"""API client for the Min Renovasjon service."""
from __future__ import annotations

import asyncio
import json
import logging
import socket
from typing import Any

import aiohttp

from .const import (
    CONST_APP_KEY,
    CONST_APP_KEY_VALUE,
    CONST_KOMMUNE_NUMMER,
    CONST_URL_FRAKSJONER,
    CONST_URL_TOMMEKALENDER,
    ADDRESS_LOOKUP_URL,
    APP_CUSTOMERS_URL,
)

_LOGGER = logging.getLogger(__name__)


class MinRenovasjonApiError(Exception):
    """Exception raised for API errors."""


class MinRenovasjonApiClient:
    """API client for Min Renovasjon."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialise the API client."""
        self._session = session

    async def async_get_tommekalender(
        self,
        kommune_nummer: str,
        gatenavn: str,
        gatekode: str,
        husnummer: str,
        fra_dato: str,
        til_dato: str,
    ) -> list[dict[str, Any]]:
        """Fetch the waste collection calendar."""
        headers = {
            CONST_KOMMUNE_NUMMER: kommune_nummer,
            CONST_APP_KEY: CONST_APP_KEY_VALUE,
        }
        url = (
            CONST_URL_TOMMEKALENDER.replace("[gatenavn]", gatenavn)
            .replace("[gatekode]", gatekode)
            .replace("[husnr]", husnummer)
            .replace("[fra_dato]", fra_dato)
            .replace("[til_dato]", til_dato)
        )
        return await self._async_get_json(url, headers=headers)

    async def async_get_fraksjoner(
        self, kommune_nummer: str
    ) -> list[dict[str, Any]]:
        """Fetch available waste fractions for a municipality."""
        headers = {
            CONST_KOMMUNE_NUMMER: kommune_nummer,
            CONST_APP_KEY: CONST_APP_KEY_VALUE,
        }
        return await self._async_get_json(CONST_URL_FRAKSJONER, headers=headers)

    async def async_municipality_is_app_customer(
        self, kommune_nummer: str
    ) -> bool:
        """Check whether the municipality supports the Min Renovasjon app."""
        params = {"Appid": "MobilOS-NorkartRenovasjon"}
        try:
            customers = await self._async_get_json(
                APP_CUSTOMERS_URL, params=params
            )
        except MinRenovasjonApiError:
            return False
        return any(c["Number"] == kommune_nummer for c in customers)

    async def async_address_lookup(
        self, search_string: str
    ) -> dict[str, Any]:
        """Look up an address via geonorge.no."""
        params = {
            "sok": search_string,
            "filtrer": (
                "adresser.kommunenummer,"
                "adresser.adressenavn,"
                "adresser.adressekode,"
                "adresser.nummer,"
                "adresser.kommunenavn,"
                "adresser.postnummer,"
                "adresser.poststed"
            ),
        }
        return await self._async_get_json(ADDRESS_LOOKUP_URL, params=params)

    async def _async_get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        """Perform a GET request and return parsed JSON."""
        try:
            async with self._session.get(
                url, params=params, headers=headers
            ) as resp:
                if not resp.ok:
                    raise MinRenovasjonApiError(
                        f"HTTP {resp.status} from {url}"
                    )
                data = await resp.read()
                return json.loads(data.decode("UTF-8"))

        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as exc:
            raise MinRenovasjonApiError(
                f"Request error: {exc} ({url})"
            ) from exc
