from dataclasses import dataclass
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from .const import *
from .entity import DruEntity


@dataclass(frozen=True, kw_only=True)
class Desc(SwitchEntityDescription):
    bit: int | None
    on_action: int
    off_action: int
    temp_control: bool = False


SWITCHES = (
    Desc(key="main_burner", name="Main burner", bit=STATUS_MAIN_BURNER, on_action=ACTION_MAIN_BURNER_ON, off_action=ACTION_MAIN_BURNER_OFF),
    Desc(key="second_burner", name="Second burner", bit=STATUS_SECOND_BURNER, on_action=ACTION_SECOND_BURNER_ON, off_action=ACTION_SECOND_BURNER_OFF),
    Desc(key="wave", name="Wave", bit=STATUS_WAVE, on_action=ACTION_WAVE_ON, off_action=ACTION_WAVE_OFF),
    Desc(key="temperature_control", name="Temperature control", bit=None, on_action=ACTION_TEMP_CONTROL_ON, off_action=ACTION_TEMP_CONTROL_OFF, temp_control=True),
)


class DruSwitch(DruEntity, SwitchEntity):
    def __init__(self, entry, description):
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def is_on(self):
        if self.entity_description.temp_control:
            return self.coordinator.data.temperature_control_state == 2
        return self.coordinator.data.status_bit(self.entity_description.bit)

    async def async_turn_on(self, **kwargs):
        await self.device.async_action(self.entity_description.on_action)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.device.async_action(self.entity_description.off_action)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(DruSwitch(entry, d) for d in SWITCHES)
