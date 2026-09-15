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
            is_transient_gateway_failure = (
                "0x0b" in error_text
                or "response timeout" in error_text
                or "timed out" in error_text
            )

            # Both Modbus exception 0x0B and a TCP/Modbus response timeout can be
            # transient symptoms of the DRU gateway/RF target not answering in time.
            # Keep the last valid values for a limited number of polls instead of
            # immediately making every Home Assistant entity unavailable.
            if is_transient_gateway_failure and self.data is not None:
                self._transient_failures += 1
                if self._transient_failures <= MAX_TRANSIENT_FAILURES:
                    _LOGGER.debug(
                        "Transient DRU communication failure (%s/%s); keeping last valid data: %s",
                        self._transient_failures,
                        MAX_TRANSIENT_FAILURES,
                        err,
                    )
                    return self.data

            raise UpdateFailed(f"Unable to read DRU fireplace: {err}") from err

        self._transient_failures = 0
        return data
