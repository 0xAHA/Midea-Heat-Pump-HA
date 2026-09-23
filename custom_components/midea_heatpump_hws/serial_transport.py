"""Serial Modbus transport for Midea Heat Pump Water Heater integration.

Covers local USB RS485 adapters and ESPHome serial proxies (e.g. Home Assistant
Connect AUX-2, esphome-hass:// URLs) via modbus-connection's tmodbus backend,
which opens ports through serialx.

A serial port can only be opened once, so every config entry (and config flow
validation) on the same port shares one ModbusConnection. Links are reference
counted and closed when the last user releases them.

SerialModbusClient mimics the small slice of pymodbus' AsyncModbusTcpClient
that the coordinator uses, so the TCP path stays on pymodbus untouched.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from modbus_connection import (
    ModbusConnectionError,
    ModbusError,
    ModbusSerialParams,
)
from modbus_connection.tmodbus import ModbusConnection

from .const import (
    DOMAIN,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_STOPBITS,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
)

_LOGGER = logging.getLogger(__name__)

# Kept outside hass.data[DOMAIN], which is keyed by config entry id only
SERIAL_LINKS_KEY = f"{DOMAIN}_serial_links"
SERIAL_LINKS_LOCK_KEY = f"{DOMAIN}_serial_links_lock"

REQUEST_TIMEOUT = 5.0


def serial_params_from_config(config: dict[str, Any]) -> ModbusSerialParams:
    """Build serial params from config entry data."""
    return ModbusSerialParams(
        device=config[CONF_SERIAL_PORT],
        baudrate=int(config.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
        bytesize=int(config.get(CONF_BYTESIZE, DEFAULT_BYTESIZE)),
        parity=config.get(CONF_PARITY, DEFAULT_PARITY),
        stopbits=int(config.get(CONF_STOPBITS, DEFAULT_STOPBITS)),
        framer="rtu",
    )


@dataclass
class _SharedLink:
    """One open serial port shared by any number of users."""

    connection: ModbusConnection
    params: ModbusSerialParams
    users: int = 0


class _Result:
    """pymodbus-style response: .registers and .isError()."""

    def __init__(self, registers: list[int] | None = None, error: Exception | None = None) -> None:
        self.registers = registers or []
        self.error = error

    def isError(self) -> bool:  # noqa: N802 - mirrors pymodbus
        return self.error is not None

    def __str__(self) -> str:
        return str(self.error) if self.error else f"registers={self.registers}"


class SerialModbusClient:
    """pymodbus-shaped adapter over a shared modbus-connection link."""

    def __init__(self, link: _SharedLink) -> None:
        self._link = link

    @property
    def connected(self) -> bool:
        return self._link.connection.connected

    async def connect(self) -> bool:
        """Open the shared link (a no-op if already open)."""
        await self._link.connection.connect()
        return self.connected

    def close(self) -> None:
        """No-op: the shared link's lifetime is owned by async_release_serial_client."""

    async def read_holding_registers(self, address: int, count: int = 1, device_id: int = 1) -> _Result:
        unit = self._link.connection.for_unit(device_id)
        try:
            return _Result(registers=await unit.read_holding_registers(address, count))
        except ModbusConnectionError:
            raise
        except ModbusError as err:
            # Exception responses, timeouts and protocol errors map to isError()
            return _Result(error=err)

    async def write_register(self, address: int, value: int, device_id: int = 1) -> _Result:
        unit = self._link.connection.for_unit(device_id)
        try:
            await unit.write_register(address, int(value))
            return _Result()
        except ModbusConnectionError:
            raise
        except ModbusError as err:
            return _Result(error=err)


def _lock(hass: HomeAssistant) -> asyncio.Lock:
    return hass.data.setdefault(SERIAL_LINKS_LOCK_KEY, asyncio.Lock())


async def async_acquire_serial_client(hass: HomeAssistant, config: dict[str, Any]) -> SerialModbusClient:
    """Get a client on the shared link for this port, opening it if needed."""
    params = serial_params_from_config(config)
    async with _lock(hass):
        links: dict[tuple[str, str], _SharedLink] = hass.data.setdefault(SERIAL_LINKS_KEY, {})
        link = links.get(params.endpoint)
        if link is None:
            link = _SharedLink(
                connection=ModbusConnection(params, timeout=REQUEST_TIMEOUT),
                params=params,
            )
            links[params.endpoint] = link
            _LOGGER.debug("Created shared serial link for %s", params.device)
        elif link.params != params:
            raise ValueError(
                f"Serial port {params.device} is already open with different line "
                f"settings ({link.params.baudrate} {link.params.bytesize}"
                f"{link.params.parity}{link.params.stopbits}); all devices on one bus "
                "must use the same settings"
            )
        link.users += 1
        _LOGGER.debug("Serial link %s now has %d user(s)", params.device, link.users)
        return SerialModbusClient(link)


async def async_release_serial_client(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Release one user of the shared link, closing it when unused."""
    params = serial_params_from_config(config)
    async with _lock(hass):
        links: dict[tuple[str, str], _SharedLink] = hass.data.get(SERIAL_LINKS_KEY, {})
        link = links.get(params.endpoint)
        if link is None:
            return
        link.users -= 1
        _LOGGER.debug("Serial link %s now has %d user(s)", params.device, link.users)
        if link.users > 0:
            return
        links.pop(params.endpoint)
        try:
            await link.connection.close()
        except ModbusError as err:
            _LOGGER.debug("Error closing serial link %s (ignored): %s", params.device, err)
