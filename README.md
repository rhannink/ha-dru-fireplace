# DRU Fireplace for Home Assistant

Custom Home Assistant integration for a DRU/Honeywell DFGT fireplace over Modbus TCP.

## Configuration

The fireplace is configured entirely through the Home Assistant UI. No fixed IP address is stored in the integration.

Go to **Settings → Devices & services → Add integration → DRU Fireplace** and enter:

- **Host / IP address** — for example `192.168.1.199`
- **Port** — default `502`
- **Unit ID** — default `2`

The integration validates the connection before creating the config entry. Connection settings are stored in Home Assistant's config entry, not in YAML or source code.

## Installation

Copy `custom_components/dru_fireplace` to `/config/custom_components/` and restart Home Assistant.

## Protocol

Registers 40200 (actions) and 40201 (requested flame height) are write-only and are never included in polling reads.
