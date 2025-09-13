"""Modbus coordinator for Midea Heat Pump Water Heater integration."""
import asyncio
import logging
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
        self.modbus_unit = config[CONF_MODBUS_UNIT]
        
        # Store register addresses
        self.power_register = config[CONF_POWER_REGISTER]
        self.mode_register = config[CONF_MODE_REGISTER]
        self.temp_register = config[CONF_TEMP_REGISTER]
        self.target_temp_register = config[CONF_TARGET_TEMP_REGISTER]
        
        # Temperature scaling
        self.temp_offset = config[CONF_TEMP_OFFSET]
        self.temp_scale = config[CONF_TEMP_SCALE]
        
        # Mode values for reverse lookup
        self.mode_values = {
            "eco": config[CONF_ECO_MODE_VALUE],
            "performance": config[CONF_PERFORMANCE_MODE_VALUE],
            "electric": config[CONF_ELECTRIC_MODE_VALUE],
        }
        self.value_to_mode = {v: k for k, v in self.mode_values.items()}
        
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
                await self._process_pending_writes()
            
            # Connect if needed
            if not self._client or not self._client.connected:
                await self._connect()
            
            data = {}
            
            # Read core registers
            async with self._lock:
                # Read power state
                power_result = await self._client.read_holding_registers(
                    address=self.power_register,
                    count=1,
                    device_id=self.modbus_unit
                )
                if not power_result.isError():
                    data["power_state"] = bool(power_result.registers[0])
                else:
                    _LOGGER.warning("Failed to read power register")
                
                # Read mode
                mode_result = await self._client.read_holding_registers(
                    address=self.mode_register,
                    count=1,
                    device_id=self.modbus_unit
                )
                if not mode_result.isError():
                    mode_value = mode_result.registers[0]
                    data["mode_value"] = mode_value
                    data["mode"] = self.value_to_mode.get(mode_value, "eco")
                else:
                    _LOGGER.warning("Failed to read mode register")
                
                # Read current temperature
                temp_result = await self._client.read_holding_registers(
                    address=self.temp_register,
                    count=1,
                    device_id=self.modbus_unit
                )
                if not temp_result.isError():
                    raw_temp = temp_result.registers[0]
                    data["current_temp"] = (raw_temp * self.temp_scale) + self.temp_offset
                    data["current_temp_raw"] = raw_temp
                else:
                    _LOGGER.warning("Failed to read temperature register")
                
                # Read target temperature
                target_result = await self._client.read_holding_registers(
                    address=self.target_temp_register,
                    count=1,
                    device_id=self.modbus_unit
                )
                if not target_result.isError():
                    data["target_temp"] = target_result.registers[0]
                else:
                    _LOGGER.warning("Failed to read target temperature register")
                
                # Determine operation state
                if data.get("power_state", False):
                    data["operation"] = data.get("mode", "eco")
                else:
                    data["operation"] = "off"
                
                # Read additional sensors if enabled
                if self.enable_additional_sensors:
                    for sensor_name, register in self.additional_registers.items():
                        if register is None:
                            continue
                        
                        try:
                            result = await self._client.read_holding_registers(
                                address=register,
                                count=1,
                                device_id=self.modbus_unit
                            )
                            
                            if not result.isError():
                                raw_value = result.registers[0]
                                
                                # Apply scaling based on sensor type
                                # Exhaust temp (105) is the only one without scaling
                                if sensor_name == "exhaust_temp":
                                    data[sensor_name] = raw_value
                                else:
                                    # All others use offset -15, scale 0.5
                                    # (tank_top, tank_bottom, condensor, outdoor, suction)
                                    data[sensor_name] = (raw_value * self.temp_scale) + self.temp_offset
                            else:
                                _LOGGER.debug("Failed to read %s register %d", sensor_name, register)
                                
                        except Exception as ex:
                            _LOGGER.debug("Error reading %s: %s", sensor_name, ex)
            
            _LOGGER.debug("Modbus data updated: %s", data)
            return data
            
        except ModbusException as err:
            raise UpdateFailed(f"Modbus communication error: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}")

    async def _connect(self) -> None:
        """Establish modbus connection."""
        try:
            if self._client:
                self._client.close()
            
            self._client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=5
            )
            
            connected = await self._client.connect()
            if not connected:
                raise UpdateFailed("Failed to connect to modbus device")
                
            _LOGGER.info("Connected to modbus device at %s:%s", self.host, self.port)
            
        except Exception as err:
            raise UpdateFailed(f"Connection failed: {err}")

    async def _process_pending_writes(self) -> None:
        """Process any pending write operations."""
        if not self._pending_writes:
            return
            
        async with self._lock:
            for operation, params in self._pending_writes.items():
                try:
                    if operation == "target_temp":
                        result = await self._client.write_register(
                            address=self.target_temp_register,
                            value=int(params),
                            device_id=self.modbus_unit
                        )
                        if result.isError():
                            _LOGGER.error("Failed to write target temperature: %s", result)
                        else:
                            _LOGGER.debug("Successfully wrote target temp = %s", params)
                    
                    elif operation == "power_state":
                        result = await self._client.write_register(
                            address=self.power_register,
                            value=1 if params else 0,
                            device_id=self.modbus_unit
                        )
                        if result.isError():
                            _LOGGER.error("Failed to write power state: %s", result)
                        else:
                            _LOGGER.debug("Successfully wrote power state = %s", params)
                    
                    elif operation == "mode":
                        if params in self.mode_values:
                            result = await self._client.write_register(
                                address=self.mode_register,
                                value=self.mode_values[params],
                                device_id=self.modbus_unit
                            )
                            if result.isError():
                                _LOGGER.error("Failed to write mode: %s", result)
                            else:
                                _LOGGER.debug("Successfully wrote mode = %s", params)
                    
                    elif operation == "operation_mode":
                        # Handle water heater operation mode changes
                        if params == "Off":
                            # Turn off power
                            result = await self._client.write_register(
                                address=self.power_register,
                                value=0,
                                device_id=self.modbus_unit
                            )
                        elif params in self.mode_values:
                            # Set mode first, then turn on power
                            mode_result = await self._client.write_register(
                                address=self.mode_register,
                                value=self.mode_values[params],
                                device_id=self.modbus_unit
                            )
                            if not mode_result.isError():
                                power_result = await self._client.write_register(
                                    address=self.power_register,
                                    value=1,
                                    device_id=self.modbus_unit
                                )
                                if power_result.isError():
                                    _LOGGER.error("Failed to turn on power after mode change")
                            else:
                                _LOGGER.error("Failed to set mode %s", params)
                        
                        _LOGGER.debug("Successfully set operation mode = %s", params)
                        
                except Exception as err:
                    _LOGGER.error("Error writing %s: %s", operation, err)
            
            # Clear pending writes after processing
            self._pending_writes.clear()

    async def write_register(self, operation: str, value: Any) -> bool:
        """Queue a register write for the next update cycle."""
        self._pending_writes[operation] = value
        
        # Trigger an immediate update to process the write
        await self.async_request_refresh()
        
        return True

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and close connections."""
        if self._client:
            self._client.close()
            self._client = None