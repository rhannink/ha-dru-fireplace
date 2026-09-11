"""Config flow for DRU Fireplace."""

import voluptuous as vol
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from modbus_connection import ModbusTcpParams

from .const import CONF_UNIT_ID, DEFAULT_PORT, DEFAULT_UNIT_ID, DOMAIN, REG_STATUS


async def _validate(hass, host: str, port: int, unit_id: int) -> None:
    """Validate the Modbus connection before saving it."""
    async with async_get_temporary_unit(
        hass, ModbusTcpParams(host=host, port=port), unit_id
    ) as unit:
        values = await unit.read_holding_registers(REG_STATUS, 1)
        if len(values) != 1:
            raise ValueError("Unexpected DRU response")


class DruFireplaceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a DRU fireplace from the Home Assistant GUI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            unit_id = user_input[CONF_UNIT_ID]

            await self.async_set_unique_id(f"{host.lower()}:{port}:{unit_id}")
            self._abort_if_unique_id_configured()

            try:
                await _validate(self.hass, host, port, unit_id)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"DRU Fireplace ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_UNIT_ID: unit_id,
                    },
                )

        defaults = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=defaults.get(CONF_HOST, "192.168.1.199"),
                ): str,
                vol.Required(
                    CONF_PORT,
                    default=defaults.get(CONF_PORT, DEFAULT_PORT),
                ): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required(
                    CONF_UNIT_ID,
                    default=defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
                ): vol.All(int, vol.Range(min=1, max=247)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
