# Min Renovasjon Kalender

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration that exposes your Norwegian waste collection schedule as a **single calendar entity** — one event per pickup day listing everything being collected.

## Credits
- **[eyesoft/home_assistant_min_renovasjon](https://github.com/eyesoft/home_assistant_min_renovasjon)** — the original Min Renovasjon integration that this project builds upon.
- **[Claude](https://claude.ai) by [Anthropic](https://www.anthropic.com)** — this integration was developed with the assistance of Claude, Anthropic's AI assistant.

## Features
- **Calendar-only** — no sensor entities, just a clean calendar
- **Grouped by pickup day** — one all-day event per date; the description lists every fraction collected that day (e.g. _"Restavfall, papir og plastemballasje"_)
- **Full-year view** — fetches all pickup dates for a configurable number of days ahead (default 365, range 30–730)
- **Lookback** — optionally include past pickup days (default 30 days back)
- **Fraction filtering** — exclude fractions like "Farlig avfall" that clutter the calendar
- **UI-based setup** — config flow with Norwegian address search, no YAML needed
- **DataUpdateCoordinator** — reduced polling (once every 7 days)

## Installation

### HACS (recommended)
1. Open HACS → **Integrations** → three-dot menu → **Custom repositories**
2. Add this repository URL with category **Integration**
   ( https://github.com/aalbretsen/min-renovasjon-kalender )
3. Search for _Min Renovasjon Kalender_ and download
4. Restart Home Assistant

### Manual
Copy the `custom_components/min_renovasjon_kalender/` folder into your Home Assistant `config/custom_components/` directory and restart.

## Setup
1. Go to **Settings → Devices & services → Add Integration**
2. Search for **Min Renovasjon Kalender**
3. Enter your address (e.g. `Min gate 12, 0153`)
4. A calendar entity `calendar.min_renovasjon` will appear

## Options
Click **Configure** on the integration card to change:

| Option | Default | Range | Description |
| --- | --- | --- | --- |
| `calendar_days` | 365 | 30–730 | How many days into the future to populate |
| `calendar_days_back` | 30 | 0–365 | How many days in the past to include |
| `event_summary` | 🗑️ Hentedag for søppel | — | Title shown on each calendar event |
| `excluded_fraction_ids` | _(none)_ | — | Fractions to hide from the calendar |

## Calendar events
Each event has:

| Field | Value |
| --- | --- |
| **Summary** | 🗑️ Hentedag for søppel _(configurable in options)_ |
| **Description** | Comma-separated fractions, e.g. _"Restavfall, papir og plastemballasje"_ |
| **Date** | All-day event on the pickup date |

## Dashboard card example

You can display the next pickup day on a dashboard using the [Mushroom](https://github.com/piitaya/lovelace-mushroom) template card. 
Install Mushroom via HACS → **Frontend** → search for _Mushroom_ and download.

Then add this card to your dashboard (YAML mode):

```yaml
type: custom:mushroom-template-card
icon: mdi:trash-can
icon_color: grey
grid_options:
  columns: 12
  rows: 1
multiline_secondary: false
tap_action:
  action: none
hold_action:
  action: none
double_tap_action:
  action: none
primary: >-
  {{ state_attr('calendar.min_renovasjon', 'description') | default('Ingen hentedag') }}
secondary: >-
  {% set start = state_attr('calendar.min_renovasjon', 'start_time') %}
  {% if start %}
    {% set pickup = start | as_datetime | as_local %}
    {% set diff = (pickup.date() - now().date()).days %}
    {% set dager = ['mandag','tirsdag','onsdag','torsdag','fredag','lørdag','søndag'] %}
    {% set maaneder = ['januar','februar','mars','april','mai','juni','juli','august','september','oktober','november','desember'] %}
    Hentes {% if diff > 1 %}om {{ diff }} dager{% elif diff == 1 %}i morgen{% else %}i dag{% endif %}, {{ dager[pickup.weekday()] }} {{ pickup.day }}. {{ maaneder[pickup.month - 1] }}
  {% endif %}
```

This shows the next pickup day with a Norwegian-formatted date, for example:

> **Restavfall, papir og plastemballasje**
> Hentes om 3 dager, torsdag 17. april

## License
[MIT](LICENSE)
