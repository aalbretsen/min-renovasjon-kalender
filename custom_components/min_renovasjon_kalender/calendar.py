"""Calendar platform for Min Renovasjon Kalender."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MinRenovasjonConfigEntry
from .coordinator import MinRenovasjonCoordinator, PickupEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MinRenovasjonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    async_add_entities([MinRenovasjonCalendar(entry.runtime_data, entry)])


class MinRenovasjonCalendar(
    CoordinatorEntity[MinRenovasjonCoordinator], CalendarEntity
):
    """Calendar entity that shows one event per waste pickup day."""

    _attr_has_entity_name = True
    _attr_name = "min_renovasjon"
    _attr_translation_key = "min_renovasjon_kalender"

    def __init__(
        self,
        coordinator: MinRenovasjonCoordinator,
        entry: MinRenovasjonConfigEntry,
    ) -> None:
        """Initialise the calendar entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        if not self.coordinator.data:
            return None
        today = date.today()
        summary = self.coordinator.event_summary
        for pickup in self.coordinator.data:
            if pickup.date >= today:
                return _pickup_to_event(pickup, summary)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        if not self.coordinator.data:
            return []
        sd = start_date.date() if isinstance(start_date, datetime) else start_date
        ed = end_date.date() if isinstance(end_date, datetime) else end_date
        summary = self.coordinator.event_summary
        return [
            _pickup_to_event(p, summary)
            for p in self.coordinator.data
            if sd <= p.date <= ed
        ]


def _pickup_to_event(pickup: PickupEvent, summary: str) -> CalendarEvent:
    """Convert a PickupEvent to a CalendarEvent."""
    return CalendarEvent(
        summary=summary,
        description=pickup.description,
        start=pickup.date,
        end=pickup.date + timedelta(days=1),
    )
