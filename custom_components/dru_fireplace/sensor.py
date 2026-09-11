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
    Desc(key="hw_type", name="Hardware type", value_fn=lambda d: d.hw_type),
    Desc(key="sw_version", name="Software version", value_fn=lambda d: d.sw_version),
    Desc(key="rf_last_seen", name="RF last seen", native_unit_of_measurement="s", value_fn=lambda d: d.rf_last_seen),
    Desc(key="rf_status", name="RF communication status", value_fn=lambda d: d.rf_status),
    Desc(key="error_code", name="Error code", value_fn=lambda d: d.error_code),
    Desc(key="gateway_rssi", name="Gateway RSSI", device_class=SensorDeviceClass.SIGNAL_STRENGTH, native_unit_of_measurement="dBm", value_fn=lambda d: d.gateway_rssi),
    Desc(key="dfgt_rssi", name="DFGT RSSI", device_class=SensorDeviceClass.SIGNAL_STRENGTH, native_unit_of_measurement="dBm", value_fn=lambda d: d.dfgt_rssi),
    Desc(key="room_temperature", name="Room temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, value_fn=lambda d: d.room_temperature),
    Desc(key="temperature_setpoint", name="Temperature setpoint", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, value_fn=lambda d: d.temperature_setpoint),
    Desc(key="temperature_control_state", name="Temperature control state", value_fn=lambda d: ("not_possible", "possible", "active", "error")[d.temperature_control_state]),
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
