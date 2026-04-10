# Min Renovasjon Kalender

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration that exposes your Norwegian waste collection schedule as a **single calendar entity** — one event per pickup day listing everything being collected.

## Credits
- **[eyesoft/home_assistant_min_renovasjon](https://github.com/eyesoft/home_assistant_min_renovasjon)** — the original Min Renovasjon integration that this project builds upon.
- **[Claude](https://claude.ai) by [Anthropic](https://www.anthropic.com)** — this integration was developed with the assistance of Claude, Anthropic's AI assistant.

## Features
- **Calendar-only** — no sensor entities, just a clean calendar
- **Grouped by pickup day** — one all-day event per date; the description lists every fraction collected that day (e.g. _"Restavfall, Papir og Plastemballasje"_)
- **Full-year view** — fetches all pickup dates for a configurable number of days ahead (default 365, range 30–730)
- **UI-based setup** — config flow with Norwegian address search, no YAML needed
- **DataUpdateCoordinator** — reduced polling (once every 7 days)

## Installation

### HACS (recommended)
1. Open HACS → **Integrations** → three-dot menu → **Custom repositories**
2. Add this repository URL with category **Integration**
3. Search for _Min Renovasjon Kalender_ and download
4. Restart Home Assistant

### Manual
Copy the `custom_components/min_renovasjon_kalender/` folder into your Home Assistant `config/custom_components/` directory and restart.

## Setup
1. Go to **Settings → Devices & services → Add Integration**
2. Search for **Min Renovasjon Kalender**
3. Enter your address (e.g. `Min gate 12, 0153`)
4. A calendar entity `calendar.minrenovasjon` will appear

## Options
Click **Configure** on the integration card to change:

| Option | Default | Range | Description |
| --- | --- | --- | --- |
| `calendar_days` | 365 | 30–730 | How many days into the future to populate |

## Calendar events
Each event has:

| Field | Value |
| --- | --- |
| **Summary** | 🗑️ Hentedag for søppel |
| **Description** | Comma-separated fractions, e.g. _"Restavfall og Matavfall"_ |
| **Date** | All-day event on the pickup date |


## License
[MIT](LICENSE)
