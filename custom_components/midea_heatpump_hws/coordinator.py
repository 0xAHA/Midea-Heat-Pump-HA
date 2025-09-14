"""Modbus coordinator for Midea Heat Pump Water Heater integration.""" 
import asyncio
import logging
import traceback
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DOMAIN,
    CONF_MODBUS_UNIT,
    CONF_SCAN_INTERVAL,
    CONF_POWER_REGISTER,
    CONF_MODE_REGISTER,
    CONF_TEMP_REGISTER,
    CONF_TARGET_TEMP_REGISTER,
    CONF_ECO_MODE_VALUE,
    CONF_PERFORMANCE_MODE_VALUE,
    CONF_ELECTRIC_MODE_VALUE,
    CONF_TEMP_OFFSET,
    CONF_TEMP_SCALE,
    CONF_TARGET_TEMP_OFFSET,
    CONF_TARGET_TEMP_SCALE,
    CONF_SENSORS_TEMP_OFFSET,
    CONF_SENSORS_TEMP_SCALE,
    CONF_ENABLE_ADDITIONAL_SENSORS,
    CONF_TANK_TOP_TEMP_REGISTER,
    CONF_TANK_BOTTOM_TEMP_REGISTER,
    CONF_CONDENSOR_TEMP_REGISTER,
    CONF_OUTDOOR_TEMP_REGISTER,
    CONF_EXHAUST_TEMP_REGISTER,
    CONF_SUCTION_TEMP_REGISTER,
)

_LOGGER = logging.getLogger(__name__)


class MideaModbusCoordinator(DataUpdateCoordinator):
    """Coordinate all modbus reads for Midea Heat Pump Water Heater."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Midea Modbus",
            update_interval=timedelta(seconds=config.get(CONF_SCAN_INTERVAL, 60)),
        )
        self.config = config
        self.host = config["host"]
        self.port = config["port"]
        self.modbus_unit = config.get(CONF_MODBUS_UNIT, 1)

        # Store register addresses
        self.power_register = config.get(CONF_POWER_REGISTER)
        self.mode_register = config.get(CONF_MODE_REGISTER)
        self.temp_register = config.get(CONF_TEMP_REGISTER)
        self.target_temp_register = config.get(CONF_TARGET_TEMP_REGISTER)

        # Temperature scaling (general sensor / temp)
        # Keep backwards compatibility: use provided CONF_TEMP_* as fallback
        self.temp_offset = config.get(CONF_TEMP_OFFSET, 0.0)
        self.temp_scale = config.get(CONF_TEMP_SCALE, 1.0)

        # Target temp scaling (for writing/reading target temp)
        self.target_temp_offset = config.get(CONF_TARGET_TEMP_OFFSET, self.temp_offset)
        self.target_temp_scale = config.get(CONF_TARGET_TEMP_SCALE, self.temp_scale)

        # Additional sensors scaling (for tank_top, tank_bottom, condensor, outdoor, suction)
        self.sensors_temp_offset = config.get(CONF_SENSORS_TEMP_OFFSET, self.temp_offset)
        self.sensors_temp_scale = config.get(CONF_SENSORS_TEMP_SCALE, self.temp_scale)

        # Mode values for reverse lookup
        self.mode_values = {
            "eco": config.get(CONF_ECO_MODE_VALUE),
            "performance": config.get(CONF_PERFORMANCE_MODE_VALUE),
            "electric": config.get(CONF_ELECTRIC_MODE_VALUE),
        }
        self.value_to_mode = {v: k for k, v in self.mode_values.items() if v is not None}

        # Additional sensors configuration
        self.enable_additional_sensors = config.get(CONF_ENABLE_ADDITIONAL_SENSORS, True)
        self.additional_registers = {}
        if self.enable_additional_sensors:
            self.additional_registers = {
                "tank_top_temp": config.get(CONF_TANK_TOP_TEMP_REGISTER),
                "tank_bottom_temp": config.get(CONF_TANK_BOTTOM_TEMP_REGISTER),
                "condensor_temp": config.get(CONF_CONDENSOR_TEMP_REGISTER),
                "outdoor_temp": config.get(CONF_OUTDOOR_TEMP_REGISTER),
                "exhaust_temp": config.get(CONF_EXHAUST_TEMP_REGISTER),
                "suction_temp": config.get(CONF_SUCTION_TEMP_REGISTER),
            }

        self._client: Optional[AsyncModbusTcpClient] = None
        self._lock = asyncio.Lock()
        self._pending_writes: Dict[str, Any] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch all data from modbus."""
        try:
            # Process any pending writes first
            if self._pending_writes:
                _LOGGER.debug("Pending writes present before read: %s", self._pending_writes)
                await self._process_pending_writes()

            # Connect if needed
            if not self._client or not self._client.connected:
                await self._connect()

            data = {}

            # Read core registers
            async with self._lock:
                # Read power state
                try:
                    power_result = await self._client.read_holding_registers(
                        address=self.power_register,
                        count=1,
                        device_id=self.modbus_unit
                    )
                    if not power_result.isError():
                        data["power_state"] = bool(power_result.registers[0])
                        _LOGGER.debug("Read power register %s -> %s", self.power_register, power_result.registers[0])
                    else:
                        _LOGGER.warning("Failed to read power register %s : %s", self.power_register, power_result)
                except Exception as ex:
                    _LOGGER.exception("Exception reading power register: %s", ex)

                # Read mode
                try:
                    mode_result = await self._client.read_holding_registers(
                        address=self.mode_register,
                        count=1,
                        device_id=self.modbus_unit
                    )
                    if not mode_result.isError():
                        mode_value = mode_result.registers[0]
                        data["mode_value"] = mode_value
                        data["mode"] = self.value_to_mode.get(mode_value, "eco")
                        _LOGGER.debug("Read mode register %s -> raw=%s mapped=%s", self.mode_register, mode_value, data["mode"])
                    else:
                        _LOGGER.warning("Failed to read mode register %s : %s", self.mode_register, mode_result)
                except Exception as ex:
                    _LOGGER.exception("Exception reading mode register: %s", ex)

                # Read current temperature (sensors use temp_scale/temp_offset by default)
                try:
                    temp_result = await self._client.read_holding_registers(
                        address=self.temp_register,
                        count=1,
                        device_id=self.modbus_unit
                    )
                    if not temp_result.isError():
                        raw_temp = temp_result.registers[0]
                        data["current_temp"] = (raw_temp * self.temp_scale) + self.temp_offset
                        data["current_temp_raw"] = raw_temp
                        _LOGGER.debug(
                            "Read temp register %s -> raw=%s scaled=%s (scale=%s offset=%s)",
                            self.temp_register, raw_temp, data["current_temp"], self.temp_scale, self.temp_offset
                        )
                    else:
                        _LOGGER.warning("Failed to read temperature register %s : %s", self.temp_register, temp_result)
                except Exception as ex:
                    _LOGGER.exception("Exception reading temperature register: %s", ex)

                # Read target temperature (apply target scaling)
                try:
                    target_result = await self._client.read_holding_registers(
                        address=self.target_temp_register,
                        count=1,
                        device_id=self.modbus_unit
                    )
                    if not target_result.isError():
                        raw_target = target_result.registers[0]
                        data["target_temp_raw"] = raw_target
                        data["target_temp"] = (raw_target * self.target_temp_scale) + self.target_temp_offset
                        _LOGGER.debug(
                            "Read target temp register %s -> raw=%s scaled=%s (scale=%s offset=%s)",
                            self.target_temp_register, raw_target, data["target_temp"],
                            self.target_temp_scale, self.target_temp_offset
                        )
                    else:
                        _LOGGER.warning("Failed to read target temperature register %s : %s", self.target_temp_register, target_result)
                except Exception as ex:
                    _LOGGER.exception("Exception reading target temperature register: %s", ex)

                # Determine operation state
                if data.get("power_state", False):
                    data["operation"] = data.get("mode", "eco")
                else:
                    data["operation"] = "off"

                # Read additional sensors if enabled
                if self.enable_additional_sensors:
                    for sensor_name, register in self.additional_registers.items():
                        if register is None:
                            _LOGGER.debug("No register configured for sensor %s, skipping", sensor_name)
                            continue

                        try:
                            result = await self._client.read_holding_registers(
                                address=register,
                                count=1,
                                device_id=self.modbus_unit
                            )

                            if not result.isError():
                                raw_value = result.registers[0]

                                # Apply correct scaling:
                                # exhaust_temp — keep raw value (as original code implied), otherwise use sensors scaling
                                if sensor_name == "exhaust_temp":
                                    data[sensor_name] = raw_value
                                    _LOGGER.debug("Read %s register %s -> raw=%s (no scaling)", sensor_name, register, raw_value)
                                else:
                                    data[sensor_name] = (raw_value * self.sensors_temp_scale) + self.sensors_temp_offset
                                    _LOGGER.debug(
                                        "Read %s register %s -> raw=%s scaled=%s (scale=%s offset=%s)",
                                        sensor_name, register, raw_value, data[sensor_name],
                                        self.sensors_temp_scale, self.sensors_temp_offset
                                    )
                            else:
                                _LOGGER.debug("Failed to read %s register %s : %s", sensor_name, register, result)
                        except Exception as ex:
                            _LOGGER.exception("Error reading %s: %s", sensor_name, ex)

            _LOGGER.debug("Modbus data updated: %s", data)
            return data

        except ModbusException as err:
            _LOGGER.exception("ModbusException during update: %s", err)
            raise UpdateFailed(f"Modbus communication error: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error: %s\n%s", err, traceback.format_exc())
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _connect(self) -> None:
        """Establish modbus connection."""
        try:
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    _LOGGER.debug("Error closing previous client (ignored)")

            self._client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=5
            )

            connected = await self._client.connect()
            if not connected:
                raise UpdateFailed("Failed to connect to modbus device")

            _LOGGER.info("Connected to modbus device at %s:%s (device_id=%s)", self.host, self.port, self.modbus_unit)

        except Exception as err:
            _LOGGER.exception("Connection failed: %s", err)
            raise UpdateFailed(f"Connection failed: {err}")

    async def _process_pending_writes(self) -> None:
        """Process any pending write operations."""
        if not self._pending_writes:
            return

        async with self._lock:
            # iterate copy so we can clear original safely
            pending = dict(self._pending_writes)
            for operation, params in pending.items():
                try:
                    if operation == "target_temp":
                        # Expect params to be the desired temperature (float or int, in human units)
                        desired_temp = float(params)
                        # Convert desired temp to register value using target scaling/offset:
                        # register_value * scale + offset = desired_temp  => register_value = (desired_temp - offset) / scale
                        try:
                            register_value = int(round((desired_temp - self.target_temp_offset) / self.target_temp_scale))
                        except Exception as ex:
                            _LOGGER.exception("Failed to compute register value for target_temp: %s", ex)
                            raise

                        _LOGGER.debug(
                            "Writing target_temp: desired=%s -> register_value=%s (scale=%s offset=%s) to reg %s (device_id=%s)",
                            desired_temp, register_value, self.target_temp_scale, self.target_temp_offset,
                            self.target_temp_register, self.modbus_unit
                        )

                        try:
                            result = await self._client.write_register(
                                address=self.target_temp_register,
                                value=register_value,
                                device_id=self.modbus_unit
                            )
                        except Exception as ex:
                            _LOGGER.exception("Exception writing target temperature register: %s", ex)
                            result = ex

                        if hasattr(result, "isError") and result.isError():
                            _LOGGER.error("Failed to write target temperature: %s", result)
                        elif isinstance(result, Exception):
                            _LOGGER.error("Failed to write target temperature (exception): %s", result)
                        else:
                            _LOGGER.info("Successfully wrote target temp register=%s value=%s (desired=%s)",
                                         self.target_temp_register, register_value, desired_temp)

                    elif operation == "power_state":
                        val = 1 if params else 0
                        _LOGGER.debug("Writing power_state -> %s to reg %s (device_id=%s)", val, self.power_register, self.modbus_unit)
                        try:
                            result = await self._client.write_register(
                                address=self.power_register,
                                value=val,
                                device_id=self.modbus_unit
                            )
                        except Exception as ex:
                            _LOGGER.exception("Exception writing power state: %s", ex)
                            result = ex

                        if hasattr(result, "isError") and result.isError():
                            _LOGGER.error("Failed to write power state: %s", result)
                        elif isinstance(result, Exception):
                            _LOGGER.error("Failed to write power state (exception): %s", result)
                        else:
                            _LOGGER.info("Successfully wrote power state = %s", params)

                    elif operation == "mode":
                        if params in self.mode_values and self.mode_values[params] is not None:
                            mode_value = self.mode_values[params]
                            _LOGGER.debug("Writing mode -> %s (raw=%s) to reg %s (device_id=%s)", params, mode_value, self.mode_register, self.modbus_unit)
                            try:
                                result = await self._client.write_register(
                                    address=self.mode_register,
                                    value=mode_value,
                                    device_id=self.modbus_unit
                                )
                            except Exception as ex:
                                _LOGGER.exception("Exception writing mode: %s", ex)
                                result = ex

                            if hasattr(result, "isError") and result.isError():
                                _LOGGER.error("Failed to write mode: %s", result)
                            elif isinstance(result, Exception):
                                _LOGGER.error("Failed to write mode (exception): %s", result)
                            else:
                                _LOGGER.info("Successfully wrote mode = %s", params)
                        else:
                            _LOGGER.error("Tried to write unknown mode: %s", params)

                    elif operation == "operation_mode":
                        # Handle water heater operation mode changes
                        if params == "Off":
                            _LOGGER.debug("operation_mode: turning Off -> writing power 0 to %s (device_id=%s)", self.power_register, self.modbus_unit)
                            try:
                                result = await self._client.write_register(
                                    address=self.power_register,
                                    value=0,
                                    device_id=self.modbus_unit
                                )
                            except Exception as ex:
                                _LOGGER.exception("Exception writing power for operation_mode Off: %s", ex)
                                result = ex

                            if hasattr(result, "isError") and result.isError():
                                _LOGGER.error("Failed to write power state for operation_mode Off: %s", result)
                            elif isinstance(result, Exception):
                                _LOGGER.error("Failed to write power state for operation_mode Off (exception): %s", result)
                            else:
                                _LOGGER.info("operation_mode: turned Off successfully")

                        elif params in self.mode_values and self.mode_values[params] is not None:
                            mode_value = self.mode_values[params]
                            _LOGGER.debug("operation_mode: setting mode %s (raw=%s) then power on", params, mode_value)
                            try:
                                mode_result = await self._client.write_register(
                                    address=self.mode_register,
                                    value=mode_value,
                                    device_id=self.modbus_unit
                                )
                            except Exception as ex:
                                _LOGGER.exception("Exception writing mode for operation_mode: %s", ex)
                                mode_result = ex

                            if hasattr(mode_result, "isError") and mode_result.isError():
                                _LOGGER.error("Failed to set mode %s: %s", params, mode_result)
                            elif isinstance(mode_result, Exception):
                                _LOGGER.error("Failed to set mode %s (exception): %s", params, mode_result)
                            else:
                                # after successful mode set, set power on
                                try:
                                    power_result = await self._client.write_register(
                                        address=self.power_register,
                                        value=1,
                                        device_id=self.modbus_unit
                                    )
                                except Exception as ex:
                                    _LOGGER.exception("Exception turning power on after mode change: %s", ex)
                                    power_result = ex

                                if hasattr(power_result, "isError") and power_result.isError():
                                    _LOGGER.error("Failed to turn on power after mode change: %s", power_result)
                                elif isinstance(power_result, Exception):
                                    _LOGGER.error("Failed to turn on power after mode change (exception): %s", power_result)
                                else:
                                    _LOGGER.info("Successfully set operation_mode = %s", params)

                    else:
                        _LOGGER.warning("Unknown pending write operation: %s", operation)

                except Exception as err:
                    _LOGGER.error("Error writing %s: %s\n%s", operation, err, traceback.format_exc())

            # Clear pending writes after processing
            self._pending_writes.clear()

    async def write_register(self, operation: str, value: Any) -> bool:
        """Queue a register write for the next update cycle."""
        _LOGGER.debug("Queueing write %s = %s", operation, value)
        self._pending_writes[operation] = value

        # Trigger an immediate update to process the write
        await self.async_request_refresh()

        return True

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and close connections."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                _LOGGER.debug("Error closing client on shutdown (ignored)")
            self._client = None
