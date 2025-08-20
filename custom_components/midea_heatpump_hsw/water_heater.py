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
    CONF_MODE_SWITCH,
    CONF_MODBUS_HUB,
    CONF_MODBUS_UNIT,
    CONF_TARGET_TEMP_REGISTER
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Generic Water Heater"


async def async_setup_platform(
    hass, hass_config, async_add_entities, discovery_info=None
):
    """Set up the generic water_heater devices."""
    entities = []

    for config in discovery_info:
        name = config[CONF_NAME]
        heater_entity_id = config[CONF_HEATER]
        sensor_entity_id = config[CONF_SENSOR]
        target_temp = config.get(CONF_TARGET_TEMP)
        temp_delta = config.get(CONF_TEMP_DELTA)
        min_temp = config.get(CONF_TEMP_MIN)
        max_temp = config.get(CONF_TEMP_MAX)
        mode_switch_entity_id = config.get(CONF_MODE_SWITCH)
        modbus_hub = config.get(CONF_MODBUS_HUB)
        modbus_unit = config.get(CONF_MODBUS_UNIT, 1)
        target_temp_register = config.get(CONF_TARGET_TEMP_REGISTER, 2)
        unit = hass.config.units.temperature_unit

        entities.append(
            GenericWaterHeater(
                name, heater_entity_id, sensor_entity_id, target_temp, temp_delta, 
                min_temp, max_temp, unit, mode_switch_entity_id, modbus_hub, 
                modbus_unit, target_temp_register
            )
        )

    async_add_entities(entities)


class GenericWaterHeater(WaterHeaterEntity, RestoreEntity):
    """Representation of a generic water_heater device."""

    def __init__(
        self, name, heater_entity_id, sensor_entity_id, target_temp, temp_delta, min_temp, max_temp, unit,
        mode_switch_entity_id=None, modbus_hub=None, modbus_unit=1, target_temp_register=2  # Add these
    ):
        """Initialize the water_heater device."""
        self._attr_name = name
        self.heater_entity_id = heater_entity_id
        self.sensor_entity_id = sensor_entity_id
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.OPERATION_MODE
        self._target_temperature = target_temp
        self._temperature_delta = temp_delta
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._unit_of_measurement = unit
        self._current_operation = STATE_ON
        self._current_temperature = None
        # Mapping between Midea names (UI) and HA standard names (internal)
        self._midea_to_ha_modes = {
            "off": "off",
            "eco": "eco", 
            #"e-heater": "electric",
            "hybrid": "performance"
        }
        self._ha_to_midea_modes = {
            "off": "off",
            "eco": "eco",
            #"electric": "e-heater",
            "performance": "hybrid"
        }
        self._operation_list = [
            "off",
            "eco", 
            #"electric",   # Electric only mode (your e-heater)
            "hybrid"  # Shows as "hybrid" in UI, maps to "performance" internally
        ]

        self._attr_available = False
        self._attr_should_poll = False
        self.mode_switch_entity_id = mode_switch_entity_id
        self._modbus_hub = modbus_hub
        self._modbus_unit = modbus_unit
        self._target_temp_register = target_temp_register

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
        """Return current operation ie. on, off."""
        return self._current_operation

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def min_temp(self):
        """Return the minimum targetable temperature."""
        """If the min temperature is not set on the config, returns the HA default for Water Heaters."""
        if not self._min_temp:
            self._min_temp = TemperatureConverter.convert(DEFAULT_MIN_TEMP, UnitOfTemperature.FAHRENHEIT, self._unit_of_measurement) 
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum targetable temperature."""
        """If the max temperature is not set on the config, returns the HA default for Water Heaters."""
        if not self._max_temp:
            self._max_temp = TemperatureConverter.convert(DEFAULT_MAX_TEMP, UnitOfTemperature.FAHRENHEIT, self._unit_of_measurement) 
        return self._max_temp

    @property
    def icon(self):
        """Return the icon for the current operation mode."""
        mode_icons = {
            "off": "mdi:power-off",
            "eco": "mdi:leaf",
            "hybrid": "mdi:speedometer",  # or "mdi:lightning-bolt" or "mdi:speedometer"
        }
        current_mode = self._ha_to_midea_modes.get(self._current_operation, self._current_operation)
        return mode_icons.get(current_mode, "mdi:water-boiler")  # Default icon

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
        # Convert Midea name to HA standard name
        ha_mode = self._midea_to_ha_modes.get(operation_mode, operation_mode)
        self._current_operation = ha_mode
        
        if ha_mode == "off":
            # Turn off main switch
            await self.hass.services.async_call(
                "switch", "turn_off", 
                {"entity_id": self.heater_entity_id}
            )
        elif ha_mode == "eco":
            # Set mode switch to off (economy) and turn on main switch
            if self.mode_switch_entity_id:
                await self.hass.services.async_call(
                    "switch", "turn_off", 
                    {"entity_id": self.mode_switch_entity_id}
                )
            await self.hass.services.async_call(
                "switch", "turn_on", 
                {"entity_id": self.heater_entity_id}
            )
        elif ha_mode == "performance":  # When user selects "hybrid"
            # Set mode switch to on (hybrid) and turn on main switch
            if self.mode_switch_entity_id:
                await self.hass.services.async_call(
                    "switch", "turn_on", 
                    {"entity_id": self.mode_switch_entity_id}
                )
            await self.hass.services.async_call(
                "switch", "turn_on", 
                {"entity_id": self.heater_entity_id}
            )
        
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.sensor_entity_id], self._async_sensor_changed
            )
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self.heater_entity_id], self._async_switch_changed
            )
        )

        old_state = await self.async_get_last_state()
        if old_state is not None:
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._target_temperature = float(old_state.attributes.get(ATTR_TEMPERATURE))
            self._current_operation = old_state.state

        temp_sensor = self.hass.states.get(self.sensor_entity_id)
        if temp_sensor and temp_sensor.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            self._current_temperature = float(temp_sensor.state)

        heater_switch = self.hass.states.get(self.heater_entity_id)
        if heater_switch and heater_switch.state not in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            self._attr_available = True

        if self.mode_switch_entity_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self.mode_switch_entity_id], self._async_switch_changed
                )
            )
        self.async_write_ha_state()

    async def _async_sensor_changed(self, event):
        """Handle temperature changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            # Failsafe
            _LOGGER.warning(
                "No Temperature information, entering Failsafe, turning off heater %s",
                self.heater_entity_id,
            )
            await self._async_heater_turn_off()
            self._current_temperature = None
        else:
            self._current_temperature = float(new_state.state)

        await self._async_control_heating()

    @callback
    def _async_switch_changed(self, event):
        """Handle heater switch state changes."""
        new_state = event.data.get("new_state")
        _LOGGER.debug(f"New switch state = {new_state}")
        
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            self._attr_available = False
        else:
            self._attr_available = True
            _LOGGER.debug("%s became Available", self.name)
            
            # Update operation based on switch states - PUT THE LOGIC HERE
            main_switch = self.hass.states.get(self.heater_entity_id)
            mode_switch = self.hass.states.get(self.mode_switch_entity_id) if self.mode_switch_entity_id else None
            
            if main_switch and main_switch.state == STATE_OFF:
                self._current_operation = "off"  # HA name stored internally
            elif main_switch and main_switch.state == STATE_ON:
                if mode_switch and mode_switch.state == STATE_ON:
                    self._current_operation = "performance"  # HA name stored internally
                else:
                    self._current_operation = "eco"  # HA name stored internally

        self.async_write_ha_state()

    async def _async_control_heating(self):
        """Update state only - no automatic control."""
        # Just update the state, no automatic heating control
        self.async_write_ha_state()

    async def _async_heater_turn_on(self):
        """Turn heater toggleable device on."""
        heater = self.hass.states.get(self.heater_entity_id)
        if heater is None or heater.state == STATE_ON:
            return

        _LOGGER.debug("Turning on heater %s", self.heater_entity_id)
        data = {ATTR_ENTITY_ID: self.heater_entity_id}
        await self.hass.services.async_call(
            HA_DOMAIN, SERVICE_TURN_ON, data, context=self._context
        )

    async def _async_heater_turn_off(self):
        """Turn heater toggleable device off."""
        heater = self.hass.states.get(self.heater_entity_id)
        if heater is None or heater.state == STATE_OFF:
            return

        _LOGGER.debug("Turning off heater %s", self.heater_entity_id)
        data = {ATTR_ENTITY_ID: self.heater_entity_id}
        await self.hass.services.async_call(
            HA_DOMAIN, SERVICE_TURN_OFF, data, context=self._context
        )
