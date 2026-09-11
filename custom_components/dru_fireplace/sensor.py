from dataclasses import dataclass
from collections.abc import Callable
from typing import Any
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from .entity import DruEntity


@dataclass(frozen=True, kw_only=True)
class Desc(SensorEntityDescription):
    value_fn: Callable[[Any], Any]


SENSORS = (
    Desc(key="hw_type", translation_key="hw_type", value_fn=lambda d: d.hw_type),
    Desc(key="sw_version", translation_key="sw_version", value_fn=lambda d: d.sw_version),
    Desc(key="rf_last_seen", translation_key="rf_last_seen", native_unit_of_measurement="s", value_fn=lambda d: d.rf_last_seen),
    Desc(key="rf_status", translation_key="rf_status", value_fn=lambda d: d.rf_status),
    Desc(key="error_code", translation_key="error_code", value_fn=lambda d: d.error_code),
    Desc(key="gateway_rssi", translation_key="gateway_rssi", device_class=SensorDeviceClass.SIGNAL_STRENGTH, native_unit_of_measurement="dBm", value_fn=lambda d: d.gateway_rssi),
    Desc(key="dfgt_rssi", translation_key="dfgt_rssi", device_class=SensorDeviceClass.SIGNAL_STRENGTH, native_unit_of_measurement="dBm", value_fn=lambda d: d.dfgt_rssi),
    Desc(key="room_temperature", translation_key="room_temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, value_fn=lambda d: d.room_temperature),
    Desc(key="temperature_control_state", translation_key="temperature_control_state", value_fn=lambda d: ("not_possible", "possible", "active", "error")[d.temperature_control_state]),
)


class DruSensor(DruEntity, SensorEntity):
    def __init__(self, entry, description):
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(DruSensor(entry, d) for d in SENSORS)
