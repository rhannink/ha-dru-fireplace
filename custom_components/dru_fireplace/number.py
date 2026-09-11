from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from .entity import DruEntity


class FlameHeight(DruEntity, NumberEntity):
    _attr_translation_key = "flame_height"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_assumed_state = True

    def __init__(self, entry):
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_flame_height"
        self._value = None

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value):
        await self.device.async_set_flame_height(int(value))
        self._value = value
        self.async_write_ha_state()


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([FlameHeight(entry)])
