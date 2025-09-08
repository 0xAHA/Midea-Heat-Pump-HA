"""Support for midea water heater units."""
import logging
import asyncio
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.components.water_heater import (
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.helpers.restore_state import RestoreEntity

from . import (
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_MODBUS_UNIT,
    CONF_SCAN_INTERVAL,
    CONF_TEMP_REGISTER,
    CONF_TARGET_TEMP_REGISTER,
    CONF_MODE_REGISTER,
    CONF_POWER_REGISTER,
    CONF_TEMP_OFFSET,
    CONF_TEMP_SCALE,
    CONF_TARGET_TEMP,
    CONF_TEMP_MIN,
    CONF_TEMP_MAX
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Midea Heatpump HWS"


async def async_setup_platform(hass, hass_config, async_add_entities, discovery_info=None):
    """Set up the midea water_heater devices."""
    entities = []

    for config in discovery_info:
        name = config.get("friendly_name", config[CONF_NAME])
        
        # Modbus connection settings
        modbus_host = config[CONF_MODBUS_HOST]
        modbus_port = config.get(CONF_MODBUS_PORT, 502)
        modbus_unit = config.get(CONF_MODBUS_UNIT, 1)
        scan_interval = config.get(CONF_SCAN_INTERVAL, 30)
        
        # Register addresses
        temp_register = config[CONF_TEMP_REGISTER]
        target_temp_register = config[CONF_TARGET_TEMP_REGISTER]
        mode_register = config[CONF_MODE_REGISTER]
        power_register = config[CONF_POWER_REGISTER]
        
        # Temperature scaling
        temp_offset = config.get(CONF_TEMP_OFFSET, 0)
        temp_scale = config.get(CONF_TEMP_SCALE, 1)
        
        # Temperature settings
        target_temp = config.get(CONF_TARGET_TEMP, 65)
        min_temp = config.get(CONF_TEMP_MIN, 40)
        max_temp = config.get(CONF_TEMP_MAX, 75)
        
        unit = hass.config.units.temperature_unit

        entities.append(
            MideaWaterHeater(
                name, modbus_host, modbus_port, modbus_unit, scan_interval,
                temp_register, target_temp_register, mode_register, power_register,
                temp_offset, temp_scale, target_temp, min_temp, max_temp, unit
            )
        )

    async_add_entities(entities)


class MideaWaterHeater(WaterHeaterEntity, RestoreEntity):
    """Representation of a Midea water heater via direct Modbus."""

    def __init__(
        self, name, modbus_host, modbus_port, modbus_unit, scan_interval,
        temp_register, target_temp_register, mode_register, power_register,
        temp_offset, temp_scale, target_temp, min_temp, max_temp, unit
    ):
        """Initialize the Midea water heater."""
        self._attr_name = name
        self._attr_unique_id = f"midea_{modbus_host}_{modbus_unit}"
        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE | 
            WaterHeaterEntityFeature.OPERATION_MODE
        )
        
        # Modbus connection settings
        self._modbus_host = modbus_host
        self._modbus_port = modbus_port
        self._modbus_unit = modbus_unit
        self._scan_interval = scan_interval
        
        # Register addresses
        self._temp_register = temp_register
        self._target_temp_register = target_temp_register
        self._mode_register = mode_register
        self._power_register = power_register
        
        # Temperature scaling
        self._temp_offset = temp_offset
        self._temp_scale = temp_scale
        
        # Temperature settings
        self._target_temperature = target_temp
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._unit_of_measurement = unit
        
        # State
        self._current_operation = "eco"
        self._current_temperature = None
        self._operation_list = ["off", "eco", "performance", "electric"]
        
        # Modbus client
        self._client = None
        self._update_task = None
        self._attr_available = False
        self._attr_should_poll = False

    @property
    def current_temperature(self):
        """Return current temperature."""
        return self._current_temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return current operation."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def min_temp(self):
        """Return the minimum targetable temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum targetable temperature."""
        return self._max_temp

    @property
    def icon(self):
        """Return the icon for the current operation mode."""
        mode_icons = {
            "off": "mdi:power-off",
            "eco": "mdi:leaf",
            "performance": "mdi:speedometer",
            "electric": "mdi:lightning-bolt"
        }
        return mode_icons.get(self._current_operation, "mdi:water-boiler")

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        
        # Initialize modbus client
        self._client = AsyncModbusTcpClient(
            host=self._modbus_host,
            port=self._modbus_port
        )
        
        # Restore previous state
        old_state = await self.async_get_last_state()
        if old_state is not None:
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._target_temperature = float(old_state.attributes.get(ATTR_TEMPERATURE))
            if old_state.state in self._operation_list:
                self._current_operation = old_state.state

        # Start polling
        await self._start_polling()

    async def async_will_remove_from_hass(self):
        """Run when entity will be removed."""
        await self._stop_polling()
        if self._client:
            await self._client.close()

    async def _start_polling(self):
        """Start the polling task."""
        if self._update_task:
            self._update_task.cancel()
        
        self._update_task = asyncio.create_task(self._polling_loop())

    async def _stop_polling(self):
        """Stop the polling task."""
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None

    async def _polling_loop(self):
        """Main polling loop."""
        while True:
            try:
                await self._update_from_modbus()
                await asyncio.sleep(self._scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as ex:
                _LOGGER.error("Error in polling loop for %s: %s", self._attr_name, ex)
                await asyncio.sleep(self._scan_interval)

    async def _update_from_modbus(self):
        """Read all values from modbus."""
        try:
            if not self._client.connected:
                await self._client.connect()
            
            # Read current temperature - CORRECTED SYNTAX
            temp_result = await self._client.read_holding_registers(
                address=self._temp_register, 
                count=1, 
                device_id=self._modbus_unit
            )
            
            # Read mode - CORRECTED SYNTAX
            mode_result = await self._client.read_holding_registers(
                address=self._mode_register, 
                count=1, 
                device_id=self._modbus_unit
            )
            
            # Read power state - CORRECTED SYNTAX  
            power_result = await self._client.read_holding_registers(
                address=self._power_register, 
                count=1, 
                device_id=self._modbus_unit
            )
            
            # Read target temperature - CORRECTED SYNTAX
            target_result = await self._client.read_holding_registers(
                address=self._target_temp_register, 
                count=1, 
                device_id=self._modbus_unit
            )

            # Process results (this part stays the same)
            if not temp_result.isError():
                raw_temp = temp_result.registers[0]
                self._current_temperature = (raw_temp * self._temp_scale) + self._temp_offset
            
            if not target_result.isError():
                self._target_temperature = target_result.registers[0]
            
            if not power_result.isError() and not mode_result.isError():
                power_state = power_result.registers[0]
                mode_value = mode_result.registers[0]
                
                if power_state == 0:
                    self._current_operation = "off"
                else:
                    # Map mode register values to HA modes
                    mode_map = {1: "eco", 2: "performance", 4: "electric"}
                    self._current_operation = mode_map.get(mode_value, "eco")
            
            self._attr_available = True
            
        except ModbusException as ex:
            _LOGGER.error("Modbus error for %s: %s", self._attr_name, ex)
            self._attr_available = False
        except Exception as ex:
            _LOGGER.error("Unexpected error for %s: %s", self._attr_name, ex)
            self._attr_available = False
        
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        try:
            if not self._client.connected:
                await self._client.connect()
            
            result = await self._client.write_register(
                    address=self._target_temp_register,
                    value=int(temperature),
                    device_id=self._modbus_unit
            )
            
            if not result.isError():
                self._target_temperature = temperature
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to set temperature for %s", self._attr_name)
                
        except Exception as ex:
            _LOGGER.error("Error setting temperature for %s: %s", self._attr_name, ex)

    async def async_set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        try:
            if not self._client.connected:
                await self._client.connect()
            
            # Map HA modes to register values
            mode_values = {"eco": 1, "performance": 2, "electric": 4}
            
            if operation_mode == "off":
                # Turn off power
                result = await self._client.write_register(
                    address=self._power_register,
                    value=0, 
                    device_id=self._modbus_unit
                )
            elif operation_mode in mode_values:
                # Set mode first, then turn on power
                mode_result = await self._client.write_register(
                    address=self._mode_register,
                    value=mode_values[operation_mode],
                    device_id=self._modbus_unit
                )
                power_result = await self._client.write_register(
                    address=self._power_register,
                    value=1, 
                    device_id=self._modbus_unit
                )
                result = mode_result  # Check mode write success
            
            if not result.isError():
                self._current_operation = operation_mode
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to set operation mode for %s", self._attr_name)
                
        except Exception as ex:
            _LOGGER.error("Error setting operation mode for %s: %s", self._attr_name, ex)