# DRU Fireplace for Home Assistant

Custom Home Assistant integration for a DRU/Honeywell DFGT fireplace over Modbus TCP.
This code is generated entirely using OpenAI ChatGPT

## Installation via HACS

This integration can be installed through HACS as a **Custom repository**.

1. Open **HACS** in Home Assistant.
2. Go to **Integrations**.
3. Open the menu in the top-right corner and select **Custom repositories**.
4. Add the following repository URL:

   `https://github.com/rhannink/ha-dru-fireplace`

5. Select **Integration** as the category and add the repository.
6. Search for **DRU Fireplace** in HACS and install it.
7. Restart Home Assistant after installation.
8. Go to **Settings → Devices & services → Add integration** and search for **DRU Fireplace**.
9. Enter the Modbus TCP connection details of your fireplace.

> **Note:** DRU Fireplace is currently installed as a HACS custom repository and is not yet part of the default HACS repository list.

## Manual installation

Copy `custom_components/dru_fireplace` to `/config/custom_components/` and restart Home Assistant.

## Configuration

The fireplace is configured entirely through the Home Assistant UI. The IP address is configurable; `192.168.1.199` is only the initial default.

Go to **Settings → Devices & services → Add integration → DRU Fireplace** and enter:

- **Host / IP address** — the IP address of your DRU/Honeywell gateway
- **Port** — default `502`
- **Unit ID** — default `2`

The integration validates the connection before creating the config entry. Connection settings are stored in Home Assistant's config entry, not in YAML.

## Protocol

Registers 40200 (actions) and 40201 (requested flame height) are write-only and are never included in polling reads.
