"""Support for Midea water heater units via config entry."""
import logging
import asyncio
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

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
    CONF_TARGET_TEMP,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_ENABLE_ADDITIONAL_SENSORS,
    CONF_TANK_TOP_TEMP_REGISTER,
    CONF_TANK_BOTTOM_TEMP_REGISTER,
    CONF_CONDENSOR_TEMP_REGISTER,
    CONF_OUTDOOR_TEMP_REGISTER,
    CONF_EXHAUST_TEMP_REGISTER,
    CONF_SUCTION_TEMP_REGISTER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea water heater from config entry."""
    config = config_entry.data
    options = config_entry.options

    # Create water heater entity
    water_heater = MideaWaterHeater(hass, config, options, config_entry.entry_id)
    async_add_entities([water_heater])


class MideaWaterHeater(WaterHeaterEntity, RestoreEntity):
    """Representation of a Midea water heater via config entry."""

    def __init__(self, hass: HomeAssistant, config: dict, options: dict, entry_id: str) -> None:
        """Initialize the Midea water heater."""
        self._config = config
        self._options = options
        self._entry_id = entry_id
        
        # Entity attributes
        self._attr_name = config.get(CONF_NAME, "Midea Heat Pump")
        self._attr_unique_id = f"midea_{config[CONF_HOST]}_{config[CONF_MODBUS_UNIT]}"
        self._attr_temperature_unit = hass.config.units.temperature_unit  # Add this line
        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE |
            WaterHeaterEntityFeature.OPERATION_MODE
        )

        # Connection settings
        self._host = config[CONF_HOST]
        self._port = config[CONF_PORT]
        self._modbus_unit = config[CONF_MODBUS_UNIT]
        self._scan_interval = options.get(CONF_SCAN_INTERVAL, config[CONF_SCAN_INTERVAL])

        # Register addresses
        self._power_register = config[CONF_POWER_REGISTER]
        self._mode_register = config[CONF_MODE_REGISTER]
        self._temp_register = config[CONF_TEMP_REGISTER]
        self._target_temp_register = config[CONF_TARGET_TEMP_REGISTER]

        # Mode values
        self._mode_values = {
            "eco": config[CONF_ECO_MODE_VALUE],
            "performance": config[CONF_PERFORMANCE_MODE_VALUE],
            "electric": config[CONF_ELECTRIC_MODE_VALUE],
        }
        
        # Reverse mapping for reading modes
        self._value_to_mode = {v: k for k, v in self._mode_values.items()}

        # Temperature settings
        self._temp_offset = config[CONF_TEMP_OFFSET]
        self._temp_scale = config[CONF_TEMP_SCALE]
        self._target_temperature = config[CONF_TARGET_TEMP]
        self._min_temp = config[CONF_MIN_TEMP]
        self._max_temp = config[CONF_MAX_TEMP]

        # Optional sensors
        self._enable_additional_sensors = options.get(
            CONF_ENABLE_ADDITIONAL_SENSORS,
            config.get(CONF_ENABLE_ADDITIONAL_SENSORS, True)
        )
        self._additional_registers = {}
        if self._enable_additional_sensors:
            self._additional_registers = {
                "tank_top_temp": config.get(CONF_TANK_TOP_TEMP_REGISTER),
                "tank_bottom_temp": config.get(CONF_TANK_BOTTOM_TEMP_REGISTER),
                "condensor_temp": config.get(CONF_CONDENSOR_TEMP_REGISTER),
                "outdoor_temp": config.get(CONF_OUTDOOR_TEMP_REGISTER),
                "exhaust_temp": config.get(CONF_EXHAUST_TEMP_REGISTER),
                "suction_temp": config.get(CONF_SUCTION_TEMP_REGISTER),
            }

        # State
        self._current_operation = "eco"
        self._current_temperature = None
        self._operation_list = ["off", "eco", "performance", "electric"]
        self._additional_attributes = {}

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

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        attributes = {}
        if self._enable_additional_sensors:
            attributes.update(self._additional_attributes)
        return attributes

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Initialize modbus client
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)

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
        if self._client and self._client.connected:
            self._client.close()  # Don't await - it's synchronous

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

            # Read core registers
            temp_result = await self._client.read_holding_registers(
                address=self._temp_register,
                count=1,
                slave=self._modbus_unit
            )

            mode_result = await self._client.read_holding_registers(
                address=self._mode_register,
                count=1,
                slave=self._modbus_unit
            )

            power_result = await self._client.read_holding_registers(
                address=self._power_register,
                count=1,
                slave=self._modbus_unit
            )

            target_result = await self._client.read_holding_registers(
                address=self._target_temp_register,
                count=1,
                slave=self._modbus_unit
            )

            # Process core results
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
                    self._current_operation = self._value_to_mode.get(mode_value, "eco")

            # Read additional sensors if enabled
            if self._enable_additional_sensors:
                await self._read_additional_sensors()

            self._attr_available = True

        except ModbusException as ex:
            _LOGGER.error("Modbus error for %s: %s", self._attr_name, ex)
            self._attr_available = False
        except Exception as ex:
            _LOGGER.error("Unexpected error for %s: %s", self._attr_name, ex)
            self._attr_available = False

        self.async_write_ha_state()

    async def _read_additional_sensors(self):
        """Read additional sensor registers."""
        for sensor_name, register in self._additional_registers.items():
            if register is None:
                continue
            
            try:
                result = await self._client.read_holding_registers(
                    address=register,
                    count=1,
                    slave=self._modbus_unit
                )
                
                if not result.isError():
                    raw_value = result.registers[0]
                    
                    # Different sensors may need different scaling
                    if sensor_name in ["tank_top_temp", "tank_bottom_temp"]:
                        # Tank temperatures use main sensor scaling
                        scaled_value = (raw_value * self._temp_scale) + self._temp_offset
                    else:
                        # Other sensors (condensor, outdoor, exhaust, suction) likely don't need scaling
                        scaled_value = raw_value
                    
                    # Add temperature unit to the attribute name for clarity
                    attr_name = f"{sensor_name}_°{self._attr_temperature_unit}"
                    self._additional_attributes[attr_name] = scaled_value
                    
            except Exception as ex:
                _LOGGER.debug("Failed to read %s register %d: %s", sensor_name, register, ex)

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
                slave=self._modbus_unit
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

            if operation_mode == "off":
                # Turn off power
                result = await self._client.write_register(
                    address=self._power_register,
                    value=0,
                    slave=self._modbus_unit
                )
            elif operation_mode in self._mode_values:
                # Set mode first, then turn on power
                mode_result = await self._client.write_register(
                    address=self._mode_register,
                    value=self._mode_values[operation_mode],
                    slave=self._modbus_unit
                )
                power_result = await self._client.write_register(
                    address=self._power_register,
                    value=1,
                    slave=self._modbus_unit
                )
                result = mode_result  # Check mode write success

            if not result.isError():
                self._current_operation = operation_mode
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to set operation mode for %s", self._attr_name)

        except Exception as ex:
            _LOGGER.error("Error setting operation mode for %s: %s", self._attr_name, ex)