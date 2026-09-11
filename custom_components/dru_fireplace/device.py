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
    REG_TEMP_SETPOINT,
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
    temperature_setpoint: float | None

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
        self._setpoint_unsupported_logged = False
        self._setpoint_invalid_logged = False

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
        ident = await self.unit.read_holding_registers(REG_HW_TYPE, 2)
        radio = await self.unit.read_holding_registers(REG_RF_LAST_SEEN, 2)
        live = await self._read_live_registers()

        temperature_setpoint = None
        try:
            setpoint = await self.unit.read_holding_registers(REG_TEMP_SETPOINT, 1)
        except Exception as err:
            # Register 40250 is optional on older DRU/Honeywell gateways. A gateway
            # may answer with Modbus exception 0x05 when temperature control is not
            # available. This must not make all other fireplace entities unavailable.
            if not self._setpoint_unsupported_logged:
                _LOGGER.info(
                    "DRU temperature setpoint register %s is unavailable: %s",
                    REG_TEMP_SETPOINT,
                    err,
                )
                self._setpoint_unsupported_logged = True
        else:
            if setpoint:
                raw_setpoint = setpoint[0]
                # The protocol specifies 0.5 °C steps and a scale factor of 10,
                # therefore every valid raw setpoint must be divisible by 5.
                # Some devices return an uninitialised/default value such as 3276;
                # do not expose such values as a real temperature in Home Assistant.
                if raw_setpoint % 5 == 0:
                    temperature_setpoint = raw_setpoint / 10.0
                    self._setpoint_invalid_logged = False
                elif not self._setpoint_invalid_logged:
                    _LOGGER.info(
                        "Ignoring invalid DRU temperature setpoint raw value %s",
                        raw_setpoint,
                    )
                    self._setpoint_invalid_logged = True
            self._setpoint_unsupported_logged = False

        return DruData(
            hw_type=ident[0],
            sw_version=ident[1],
            rf_last_seen=radio[0],
            rf_status=radio[1],
            status=live[0],
            error_code=live[1],
            gateway_rssi=live[2] * -0.5,
            dfgt_rssi=live[3] * -0.5,
            room_temperature=live[4] / 10.0,
            temperature_setpoint=temperature_setpoint,
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

    async def async_set_temperature(self, value: float) -> None:
        raw = round(value * 10)
        if abs(raw / 10 - value) > 1e-9 or raw % 5:
            raise ValueError("Temperature must use 0.5 °C steps")
        await self._write(REG_TEMP_SETPOINT, raw)
