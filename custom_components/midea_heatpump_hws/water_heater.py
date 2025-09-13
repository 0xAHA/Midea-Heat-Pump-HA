"""Support for Midea water heater units via config entry."""
import logging
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_MODBUS_UNIT,
    CONF_TARGET_TEMP,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_ENABLE_ADDITIONAL_SENSORS,
)
from .coordinator import MideaModbusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea water heater from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]
    options = config_entry.options

    # Create water heater entity
    water_heater = MideaWaterHeater(
        coordinator,
        config,
        options,
        config_entry.entry_id
    )
    async_add_entities([water_heater])


class MideaWaterHeater(CoordinatorEntity, WaterHeaterEntity, RestoreEntity):
    """Representation of a Midea water heater via config entry."""

    def __init__(
        self,
        coordinator: MideaModbusCoordinator,
        config: dict,
        options: dict,
        entry_id: str
    ) -> None:
        """Initialize the Midea water heater."""
        super().__init__(coordinator)
        self._config = config
        self._options = options
        self._entry_id = entry_id
        
        # Entity attributes
        self._attr_name = config.get(CONF_NAME, "Midea Heat Pump")
        self._attr_unique_id = f"midea_{config['host']}_{config[CONF_MODBUS_UNIT]}"
        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE |
            WaterHeaterEntityFeature.OPERATION_MODE
        )

        # Temperature settings
        self._target_temperature = config[CONF_TARGET_TEMP]
        self._min_temp = config[CONF_MIN_TEMP]
        self._max_temp = config[CONF_MAX_TEMP]

        # Optional sensors
        self._enable_additional_sensors = options.get(
            CONF_ENABLE_ADDITIONAL_SENSORS,
            config.get(CONF_ENABLE_ADDITIONAL_SENSORS, True)
        )

        # Operation list
        self._operation_list = ["off", "eco", "performance", "electric"]

    @property
    def device_info(self):
        """Return device info to link this water heater to the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config['host']}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config['host']})",
            "manufacturer": "Midea",
            "model": "Heat Pump Water Heater",
        }
    
    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self.hass.config.units.temperature_unit
    
    @property
    def current_temperature(self):
        """Return current temperature."""
        if self.coordinator.data:
            return self.coordinator.data.get("current_temp")
        return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.coordinator.data:
            return self.coordinator.data.get("target_temp", self._target_temperature)
        return self._target_temperature

    @property
    def current_operation(self):
        """Return current operation."""
        if self.coordinator.data:
            return self.coordinator.data.get("operation", "Off")
        return "Off"

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
        current_op = self.current_operation
        return mode_icons.get(current_op, "mdi:water-boiler")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        attributes = {}
        if self._enable_additional_sensors and self.coordinator.data:
            # Add temperature sensors from coordinator data
            sensor_names = [
                "tank_top_temp",
                "tank_bottom_temp",
                "condensor_temp",
                "outdoor_temp",
                "exhaust_temp",
                "suction_temp",
            ]
            for sensor_name in sensor_names:
                if sensor_name in self.coordinator.data:
                    # Add temperature unit to the attribute name for clarity
                    attr_name = f"{sensor_name}_{self.temperature_unit}"
                    attributes[attr_name] = self.coordinator.data[sensor_name]
        return attributes

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Restore previous state
        old_state = await self.async_get_last_state()
        if old_state is not None:
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._target_temperature = float(old_state.attributes.get(ATTR_TEMPERATURE))

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self.coordinator.write_register("target_temp", temperature)

    async def async_set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        await self.coordinator.write_register("operation_mode", operation_mode)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()