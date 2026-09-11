"""DRU Fireplace integration."""

from dataclasses import dataclass
from homeassistant.components.modbus import async_get_unit
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from modbus_connection import ModbusTcpParams

from .const import CONF_UNIT_ID
from .coordinator import DruCoordinator
from .device import DruFireplaceDevice

PLATFORMS = ["sensor", "binary_sensor", "switch", "number"]


@dataclass(slots=True)
class DruRuntimeData:
    device: DruFireplaceDevice
    coordinator: DruCoordinator


type DruConfigEntry = ConfigEntry[DruRuntimeData]


async def async_setup_entry(hass, entry: DruConfigEntry) -> bool:
    unit = async_get_unit(
        hass,
        entry,
        ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
        entry.data[CONF_UNIT_ID],
    )
    device = DruFireplaceDevice(unit)
    coordinator = DruCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = DruRuntimeData(device, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry: DruConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
