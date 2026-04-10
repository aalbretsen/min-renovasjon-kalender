"""Min Renovasjon Kalender – calendar-only waste collection integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MinRenovasjonCoordinator

PLATFORMS: list[Platform] = [Platform.CALENDAR]

type MinRenovasjonConfigEntry = ConfigEntry[MinRenovasjonCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: MinRenovasjonConfigEntry
) -> bool:
    """Set up Min Renovasjon Kalender from a config entry."""
    coordinator = MinRenovasjonCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: MinRenovasjonConfigEntry
) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: MinRenovasjonConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
