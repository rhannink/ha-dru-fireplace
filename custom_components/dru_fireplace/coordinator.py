"""DRU Fireplace data coordinator."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .device import DruData, DruFireplaceDevice

_LOGGER = logging.getLogger(__name__)

MAX_TRANSIENT_FAILURES = 5
MAX_RETRY_INTERVAL = timedelta(minutes=5)


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

            if is_transient_gateway_failure:
                self._transient_failures += 1
                # Let the gateway recover instead of repeating an expensive
                # request every 30 seconds. Restore the normal cadence on success.
                self.update_interval = min(
                    SCAN_INTERVAL * (2 ** min(self._transient_failures, 4)),
                    MAX_RETRY_INTERVAL,
                )
                if self.data is not None and self._transient_failures <= MAX_TRANSIENT_FAILURES:
                    _LOGGER.debug(
                        "Transient DRU communication failure (%s/%s); keeping last valid data; "
                        "next poll in %s: %s",
                        self._transient_failures,
                        MAX_TRANSIENT_FAILURES,
                        self.update_interval,
                        err,
                    )
                    return self.data

            raise UpdateFailed(f"Unable to read DRU fireplace: {err}") from err

        self._transient_failures = 0
        self.update_interval = SCAN_INTERVAL
        return data
