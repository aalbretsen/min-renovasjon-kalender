"""DataUpdateCoordinator for Min Renovasjon Kalender."""
from __future__ import annotations

import logging
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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

UPDATE_INTERVAL = timedelta(days=7)


@dataclass
class PickupEvent:
    """A single pickup-day event with all fractions grouped."""

    date: date
    description: str
    fractions: list[str]


class MinRenovasjonCoordinator(DataUpdateCoordinator[list[PickupEvent]]):
    """Coordinator that fetches and groups waste pickup data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )
        self._street_name = urllib.parse.quote(
            urllib.parse.unquote(entry.data[CONF_STREET_NAME])
        )
        self._street_code = entry.data[CONF_STREET_CODE]
        self._house_no = entry.data[CONF_HOUSE_NO]
        self._county_id = entry.data[CONF_COUNTY_ID]

    @property
    def calendar_days(self) -> int:
        """Return the configured lookahead in days."""
        return self.config_entry.options.get(
            CONF_CALENDAR_DAYS, DEFAULT_CALENDAR_DAYS
        )

    @property
    def calendar_days_back(self) -> int:
        """Return the configured lookback in days."""
        return self.config_entry.options.get(
            CONF_CALENDAR_DAYS_BACK, DEFAULT_CALENDAR_DAYS_BACK
        )

    @property
    def excluded_fraction_ids(self) -> set[int]:
        """Return the set of fraction IDs to exclude."""
        ids = self.config_entry.options.get(CONF_EXCLUDED_FRACTION_IDS, [])
        return {int(fid) for fid in ids}

    async def _async_update_data(self) -> list[PickupEvent]:
        """Fetch data from the API and return grouped pickup events."""
        session = async_get_clientsession(self.hass)
        client = MinRenovasjonApiClient(session)

        fra_dato = (date.today() - timedelta(days=self.calendar_days_back)).strftime("%Y-%m-%d")
        til_dato = (date.today() + timedelta(days=self.calendar_days)).strftime("%Y-%m-%d")

        try:
            tommekalender = await client.async_get_tommekalender(
                self._county_id,
                self._street_name,
                self._street_code,
                self._house_no,
                fra_dato,
                til_dato,
            )
            fraksjoner = await client.async_get_fraksjoner(self._county_id)
        except MinRenovasjonApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if not tommekalender or not fraksjoner:
            raise UpdateFailed("Empty response from Min Renovasjon API")

        return _build_pickup_events(
            tommekalender, fraksjoner, self.excluded_fraction_ids
        )


def _build_pickup_events(
    tommekalender: list[dict[str, Any]],
    fraksjoner: list[dict[str, Any]],
    excluded_fraction_ids: set[int] | None = None,
) -> list[PickupEvent]:
    """Parse API data and group fractions by pickup date."""
    if excluded_fraction_ids is None:
        excluded_fraction_ids = set()

    # Build fraction-id → name map
    frac_names: dict[int, str] = {
        int(f["Id"]): f["Navn"] for f in fraksjoner
    }

    # Group fraction names by date
    date_fractions: dict[date, list[str]] = defaultdict(list)
    for entry in tommekalender:
        frac_id = int(entry["FraksjonId"])
        if frac_id in excluded_fraction_ids:
            continue
        name = frac_names.get(frac_id, f"Ukjent ({frac_id})")
        for dt_str in entry.get("Tommedatoer", []):
            if not dt_str:
                continue
            try:
                d = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S").date()
            except ValueError:
                _LOGGER.debug("Could not parse date: %s", dt_str)
                continue
            if name not in date_fractions[d]:
                date_fractions[d].append(name)

    # Build sorted list of PickupEvent
    events: list[PickupEvent] = []
    for pickup_date in sorted(date_fractions):
        fracs = sorted(date_fractions[pickup_date])
        if len(fracs) == 1:
            desc = fracs[0]
        elif len(fracs) == 2:
            desc = f"{fracs[0]} og {fracs[1]}"
        else:
            desc = ", ".join(fracs[:-1]) + " og " + fracs[-1]
        events.append(PickupEvent(date=pickup_date, description=desc, fractions=fracs))

    return events
