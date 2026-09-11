"""DRU Fireplace data coordinator."""

import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, SCAN_INTERVAL
from .device import DruData, DruFireplaceDevice

_LOGGER = logging.getLogger(__name__)


class DruCoordinator(DataUpdateCoordinator[DruData]):
    def __init__(self, hass, device: DruFireplaceDevice) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.device = device

    async def _async_update_data(self) -> DruData:
        try:
            return await self.device.async_read()
        except Exception as err:
            raise UpdateFailed(f"Unable to read DRU fireplace: {err}") from err
