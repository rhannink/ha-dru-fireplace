"""DRU Fireplace data coordinator."""

import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .device import DruData, DruFireplaceDevice

_LOGGER = logging.getLogger(__name__)

MAX_TRANSIENT_FAILURES = 5


class DruCoordinator(DataUpdateCoordinator[DruData]):
    def __init__(self, hass, device: DruFireplaceDevice) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.device = device
        self._transient_failures = 0

    async def _async_update_data(self) -> DruData:
        try:
            data = await self.device.async_read()
        except Exception as err:
            error_text = str(err).lower()
            is_gateway_timeout = "0x0b" in error_text

            # Modbus exception 0x0B means that the gateway could not get a response
            # from its target device. The DRU RF link can occasionally do this even
            # though the connection recovers on the next poll. Keep the last valid
            # values for a limited number of polls instead of immediately making all
            # Home Assistant entities unavailable.
            if is_gateway_timeout and self.data is not None:
                self._transient_failures += 1
                if self._transient_failures <= MAX_TRANSIENT_FAILURES:
                    _LOGGER.debug(
                        "Transient DRU gateway timeout (%s/%s); keeping last valid data: %s",
                        self._transient_failures,
                        MAX_TRANSIENT_FAILURES,
                        err,
                    )
                    return self.data

            self._transient_failures = 0
            raise UpdateFailed(f"Unable to read DRU fireplace: {err}") from err

        self._transient_failures = 0
        return data
