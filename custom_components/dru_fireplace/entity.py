from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


class DruEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry):
        super().__init__(entry.runtime_data.coordinator)
        self.entry = entry
        self.device = entry.runtime_data.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="DRU / Honeywell",
            model="DFGT Modbus Fireplace",
            name="DRU Fireplace",
        )
