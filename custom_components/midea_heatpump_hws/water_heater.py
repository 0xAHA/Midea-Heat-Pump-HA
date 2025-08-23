"""Support for midea water heater units."""
import logging

from homeassistant.components.water_heater import (
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import DOMAIN as HA_DOMAIN, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter

from . import (
    CONF_HEATER, 
    CONF_SENSOR, 
    CONF_TARGET_TEMP, 
    CONF_TEMP_DELTA, 
    CONF_TEMP_MIN, 
    CONF_TEMP_MAX,
    CONF_MODE_SENSOR,
    CONF_MODBUS_HUB,
    CONF_MODBUS_UNIT,
    CONF_TARGET_TEMP_REGISTER
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Midea Heatpump HWS"


async def async_setup_platform(
    hass, hass_config, async_add_entities, discovery_info=None
):
    """Set up the generic water_heater devices."""
    entities = []

    for config in discovery_info:
        name = config[CONF_NAME]
        heater_entity_id = config[CONF_HEATER]
        sensor_entity_id = config[CONF_SENSOR]
        mode_sensor_entity_id = config.get(CONF_MODE_SENSOR)
        target_temp = config.get(CONF_TARGET_TEMP)
        temp_delta = config.get(CONF_TEMP_DELTA)
        min_temp = config.get(CONF_TEMP_MIN)
        max_temp = config.get(CONF_TEMP_MAX)
        modbus_hub = config.get(CONF_MODBUS_HUB)
        modbus_unit = config.get(CONF_MODBUS_UNIT, 1)
        target_temp_register = config.get(CONF_TARGET_TEMP_REGISTER, 2)
        unit = hass.config.units.temperature_unit

        entities.append(
            GenericWaterHeater(
                name, heater_entity_id, sensor_entity_id, target_temp, temp_delta, 
                min_temp, max_temp, unit, mode_sensor_entity_id, modbus_hub, 
                modbus_unit, target_temp_register
            )
        )

    async_add_entities(entities)


class GenericWaterHeater(WaterHeaterEntity, RestoreEntity):
    """Representation of a generic water_heater device."""

    def __init__(
        self, name, heater_entity_id, sensor_entity_id, target_temp, temp_delta, min_temp, max_temp, unit,
        mode_sensor_entity_id=None, modbus_hub=None, modbus_unit=1, target_temp_register=2
    ):
        """Initialize the water_heater device."""
        self._attr_name = name
        self.heater_entity_id = heater_entity_id
        self.sensor_entity_id = sensor_entity_id
        self.mode_sensor_entity_id = mode_sensor_entity_id
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.OPERATION_MODE
        self._target_temperature = target_temp
        self._temperature_delta = temp_delta
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._unit_of_measurement = unit
        self._current_operation = "eco"  # Start with eco mode
        self._current_temperature = None
        self._modbus_hub = modbus_hub
        self._modbus_unit = modbus_unit
        self._target_temp_register = target_temp_register
        
        self._operation_list = [
            "off",
            "eco",        # Value 0
            "performance", # Value 1 - Hybrid mode
            "electric"    # Value 4 - E-Heater mode
        ]

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
        if not self._min_temp:
            self._min_temp = TemperatureConverter.convert(DEFAULT_MIN_TEMP, UnitOfTemperature.FAHRENHEIT, self._unit_of_measurement) 
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum targetable temperature."""
        if not self._max_temp:
            self._max_temp = TemperatureConverter.convert(DEFAULT_MAX_TEMP, UnitOfTemperature.FAHRENHEIT, self._unit_of_measurement) 
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

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        self._target_temperature = temperature
    
        # Write to modbus register if configured
        if self._modbus_hub and self._target_temp_register:
            await self.hass.services.async_call(
                "modbus", "write_register",
                {
                    "hub": self._modbus_hub,
                    "unit": self._modbus_unit,
                    "address": self._target_temp_register,
                    "value": int(temperature)
                }
            )
    
        self.async_write_ha_state()
    
    async def async_set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        self._current_operation = operation_mode
        
        # Map HA modes to register values
        mode_values = {
            "eco": 1,
            "performance": 2, 
            "electric": 4
        }
        
        if operation_mode == "off":
            # Turn off main switch
            await self.hass.services.async_call(
                "switch", "turn_off", 
                {"entity_id": self.heater_entity_id}
            )
        elif operation_mode in mode_values:
            # Write mode value to register and turn on main switch
            if self._modbus_hub:
                await self.hass.services.async_call(
                    "modbus", "write_register",
                    {
                        "hub": self._modbus_hub,
                        "unit": self._modbus_unit,
                        "address": 1,  # Your mode register
                        "value": mode_values[operation_mode]
                    }
                )
            await self.hass.services.async_call(
                "switch", "turn_on", 
                {"entity_id": self.heater_entity_id}
            )
        
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Track temperature sensor changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.sensor_entity_id], self._async_sensor_changed
            )
        )
        
        # Track main switch changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.heater_entity_id], self._async_switch_changed
            )
        )

        # Track mode sensor changes if configured
        if self.mode_sensor_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.mode_sensor_entity_id], self._async_mode_sensor_changed
                )
            )

        # Restore previous state
        old_state = await self.async_get_last_state()
        if old_state is not None:
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._target_temperature = float(old_state.attributes.get(ATTR_TEMPERATURE))
            if old_state.state in self._operation_list:
                self._current_operation = old_state.state

        # Initialize current temperature
        temp_sensor = self.hass.states.get(self.sensor_entity_id)
        if temp_sensor and temp_sensor.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._current_temperature = float(temp_sensor.state)

        # Initialize availability based on main switch
        heater_switch = self.hass.states.get(self.heater_entity_id)
        if heater_switch and heater_switch.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_available = True

        # Initialize current operation based on mode sensor
        if self.mode_sensor_entity_id:
            mode_sensor = self.hass.states.get(self.mode_sensor_entity_id)
            if mode_sensor and mode_sensor.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                mode_value = int(mode_sensor.state)
                mode_map = {1: "eco", 2: "performance", 4: "electric"}
                if mode_value in mode_map:
                    self._current_operation = mode_map[mode_value]

        self.async_write_ha_state()

    async def _async_sensor_changed(self, event):
        """Handle temperature sensor changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            # Failsafe - sensor unavailable
            _LOGGER.warning(
                "Temperature sensor unavailable for %s, entering failsafe",
                self._attr_name
            )
            self._current_temperature = None
        else:
            try:
                self._current_temperature = float(new_state.state)
            except (ValueError, TypeError):
                _LOGGER.error("Invalid temperature value: %s", new_state.state)
                self._current_temperature = None

        self.async_write_ha_state()

    async def _async_mode_sensor_changed(self, event):
        """Handle mode sensor changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        
        try:
            # Map register values to HA modes
            mode_map = {
                1: "eco",
                2: "performance", 
                4: "electric"
            }
            
            mode_value = int(new_state.state)
            new_mode = mode_map.get(mode_value)
            
            if new_mode and new_mode != self._current_operation:
                # Also check if main switch is on
                main_switch = self.hass.states.get(self.heater_entity_id)
                if main_switch and main_switch.state == STATE_OFF:
                    self._current_operation = "off"
                else:
                    self._current_operation = new_mode
                self.async_write_ha_state()
        except (ValueError, TypeError):
            _LOGGER.error("Invalid mode sensor value: %s", new_state.state)

    @callback
    def _async_switch_changed(self, event):
        """Handle heater switch state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_available = False
        else:
            self._attr_available = True
            
            # Update operation based on switch state
            if new_state.state == STATE_OFF:
                self._current_operation = "off"
            elif new_state.state == STATE_ON and self._current_operation == "off":
                # Switch turned on, determine mode from mode sensor
                if self.mode_sensor_entity_id:
                    mode_sensor = self.hass.states.get(self.mode_sensor_entity_id)
                    if mode_sensor and mode_sensor.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                        try:
                            mode_value = int(mode_sensor.state)
                            mode_map = {1: "eco", 2: "performance", 4: "electric"}
                            self._current_operation = mode_map.get(mode_value, "eco")
                        except (ValueError, TypeError):
                            self._current_operation = "eco"
                    else:
                        self._current_operation = "eco"  # Default to eco

        self.async_write_ha_state()