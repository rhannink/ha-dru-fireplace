"""DRU fireplace Modbus protocol wrapper."""

import asyncio
from dataclasses import dataclass
from time import monotonic
from modbus_connection import ModbusUnit

from .const import MIN_WRITE_INTERVAL, REG_ACTION, REG_FLAME_HEIGHT, REG_HW_TYPE, REG_RF_LAST_SEEN, REG_STATUS, REG_TEMP_SETPOINT


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
    temperature_setpoint: float

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

    async def async_read(self) -> DruData:
        ident = await self.unit.read_holding_registers(REG_HW_TYPE, 2)
        radio = await self.unit.read_holding_registers(REG_RF_LAST_SEEN, 2)
        live = await self.unit.read_holding_registers(REG_STATUS, 5)
        setpoint = await self.unit.read_holding_registers(REG_TEMP_SETPOINT, 1)
        return DruData(
            hw_type=ident[0], sw_version=ident[1],
            rf_last_seen=radio[0], rf_status=radio[1], status=live[0],
            error_code=live[1], gateway_rssi=live[2] * -0.5,
            dfgt_rssi=live[3] * -0.5, room_temperature=live[4] / 10.0,
            temperature_setpoint=setpoint[0] / 10.0,
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
