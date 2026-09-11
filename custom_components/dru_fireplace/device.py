"""DRU fireplace Modbus protocol wrapper."""

import asyncio
import logging
from dataclasses import dataclass
from time import monotonic

from modbus_connection import ModbusUnit

from .const import (
    MIN_WRITE_INTERVAL,
    REG_ACTION,
    REG_FLAME_HEIGHT,
    REG_HW_TYPE,
    REG_RF_LAST_SEEN,
    REG_STATUS,
)

_LOGGER = logging.getLogger(__name__)

LIVE_READ_RETRIES = 3
LIVE_READ_RETRY_DELAY = 0.5


@dataclass(slots=True)
class DruData:
    hw_type: int
    sw_version: int
    rf_last_seen: int
    rf_status: int
    status: int
    error_code: int
    gateway_rssi: float
    dfgt_rssi: float
    room_temperature: float

    def status_bit(self, bit: int) -> bool:
        return bool(self.status & (1 << bit))

    @property
    def temperature_control_state(self) -> int:
        return (self.status >> 13) & 0b11


class DruFireplaceDevice:
    def __init__(self, unit: ModbusUnit) -> None:
        self.unit = unit
        self._lock = asyncio.Lock()
        self._last_write = 0.0
        self._ident: tuple[int, int] | None = None

    async def _read_live_registers(self) -> list[int]:
        """Read live fireplace registers, retrying transient gateway failures."""
        last_error: Exception | None = None

        for attempt in range(1, LIVE_READ_RETRIES + 1):
            try:
                return await self.unit.read_holding_registers(REG_STATUS, 5)
            except Exception as err:
                last_error = err
                if attempt == LIVE_READ_RETRIES:
                    break

                _LOGGER.debug(
                    "DRU live status read failed (attempt %s/%s): %s; retrying",
                    attempt,
                    LIVE_READ_RETRIES,
                    err,
                )
                await asyncio.sleep(LIVE_READ_RETRY_DELAY)

        assert last_error is not None
        raise last_error

    async def async_read(self) -> DruData:
        # Read the live data first, because this is the most important data and the
        # RF-linked target can occasionally return Modbus exception 0x0B.
        live = await self._read_live_registers()

        # Hardware type and software version are static. Cache them after the first
        # successful read to reduce the number of Modbus requests to the gateway.
        if self._ident is None:
            ident = await self.unit.read_holding_registers(REG_HW_TYPE, 2)
            self._ident = (ident[0], ident[1])

        radio = await self.unit.read_holding_registers(REG_RF_LAST_SEEN, 2)

        return DruData(
            hw_type=self._ident[0],
            sw_version=self._ident[1],
            rf_last_seen=radio[0],
            rf_status=radio[1],
            status=live[0],
            error_code=live[1],
            gateway_rssi=live[2] * -0.5,
            dfgt_rssi=live[3] * -0.5,
            room_temperature=live[4] / 10.0,
        )

    async def _write(self, address: int, value: int) -> None:
        async with self._lock:
            wait = MIN_WRITE_INTERVAL - (monotonic() - self._last_write)
            if wait > 0:
                await asyncio.sleep(wait)
            await self.unit.write_register(address, value)
            self._last_write = monotonic()

    async def async_action(self, action: int) -> None:
        await self._write(REG_ACTION, action)

    async def async_set_flame_height(self, value: int) -> None:
        if not 0 <= value <= 100:
            raise ValueError("Flame height must be 0..100")
        await self._write(REG_FLAME_HEIGHT, value)
