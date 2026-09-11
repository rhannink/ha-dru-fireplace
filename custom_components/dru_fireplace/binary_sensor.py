from dataclasses import dataclass
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription, BinarySensorDeviceClass
from .const import *
from .entity import DruEntity


@dataclass(frozen=True, kw_only=True)
class Desc(BinarySensorEntityDescription):
    bit: int


BINARY = (
    Desc(key="fault", name="Fault", bit=STATUS_ERROR, device_class=BinarySensorDeviceClass.PROBLEM),
    Desc(key="low_battery", name="Low battery", bit=STATUS_LOW_BATTERY, device_class=BinarySensorDeviceClass.BATTERY),
    Desc(key="mains_fault", name="230 V fault", bit=STATUS_MAINS_FAULT, device_class=BinarySensorDeviceClass.PROBLEM),
    Desc(key="reset_allowed", name="Reset allowed", bit=STATUS_RESET_ALLOWED),
    Desc(key="flame_height_locked", name="Flame height locked", bit=STATUS_FLAME_HEIGHT_LOCKED),
    Desc(key="remote_bound", name="Remote control bound", bit=STATUS_REMOTE_BOUND),
    Desc(key="gateway_bound", name="Gateway bound", bit=STATUS_GATEWAY_BOUND),
    Desc(key="ignition_not_allowed", name="Ignition not allowed", bit=STATUS_IGNITION_NOT_ALLOWED, device_class=BinarySensorDeviceClass.PROBLEM),
)


class DruBinary(DruEntity, BinarySensorEntity):
    def __init__(self, entry, description):
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self):
        return self.coordinator.data.status_bit(self.entity_description.bit)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(DruBinary(entry, d) for d in BINARY)
