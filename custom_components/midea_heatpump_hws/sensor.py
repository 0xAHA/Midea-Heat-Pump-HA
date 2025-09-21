"""Support for Midea Heat Pump temperature sensors."""
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_MODBUS_UNIT,
    CONF_TEMP_REGISTER,
    CONF_TARGET_TEMP_REGISTER,
    CONF_ENABLE_ADDITIONAL_SENSORS,
    CONF_TANK_TOP_TEMP_REGISTER,
    CONF_TANK_BOTTOM_TEMP_REGISTER,
    CONF_CONDENSOR_TEMP_REGISTER,
    CONF_OUTDOOR_TEMP_REGISTER,
    CONF_EXHAUST_TEMP_REGISTER,
    CONF_SUCTION_TEMP_REGISTER,
)
from .coordinator import MideaModbusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea temperature sensors from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]
    
    entities = []
    
    # Include host in entity names to make them unique
    host_suffix = f" ({config['host']})"
    
    # Main temperature sensor
    entities.append(
        MideaTemperatureSensor(
            coordinator,
            config,
            "current_temp",
            f"Current Temperature{host_suffix}",
            config[CONF_TEMP_REGISTER],
            use_scaling=True
        )
    )
    
    # Target temperature sensor (read-only)
    entities.append(
        MideaTemperatureSensor(
            coordinator,
            config,
            "target_temp",
            f"Target Temperature{host_suffix}",
            config[CONF_TARGET_TEMP_REGISTER],
            use_scaling=False
        )
    )
    
    # Additional temperature sensors if enabled
    if config.get(CONF_ENABLE_ADDITIONAL_SENSORS, True):
        sensor_configs = [
            ("tank_top_temp", f"Tank Top Temperature{host_suffix}", config.get(CONF_TANK_TOP_TEMP_REGISTER), True),
            ("tank_bottom_temp", f"Tank Bottom Temperature{host_suffix}", config.get(CONF_TANK_BOTTOM_TEMP_REGISTER), True),
            ("condensor_temp", f"Condensor Temperature{host_suffix}", config.get(CONF_CONDENSOR_TEMP_REGISTER), False),
            ("outdoor_temp", f"Outdoor Temperature{host_suffix}", config.get(CONF_OUTDOOR_TEMP_REGISTER), False),
            ("exhaust_temp", f"Exhaust Gas Temperature{host_suffix}", config.get(CONF_EXHAUST_TEMP_REGISTER), False),
            ("suction_temp", f"Suction Temperature{host_suffix}", config.get(CONF_SUCTION_TEMP_REGISTER), False),
        ]
        
        for sensor_id, name, register, use_scaling in sensor_configs:
            if register is not None:
                entities.append(
                    MideaTemperatureSensor(
                        coordinator,
                        config,
                        sensor_id,
                        name,
                        register,
                        use_scaling
                    )
                )
    
    async_add_entities(entities)


class MideaTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Midea temperature sensor."""

    def __init__(
        self,
        coordinator: MideaModbusCoordinator,
        config: dict,
        sensor_id: str,
        name: str,
        register: int,
        use_scaling: bool
    ):
        """Initialize the temperature sensor."""
        super().__init__(coordinator)
        self._config = config
        self._sensor_id = sensor_id
        self._register = register
        self._use_scaling = use_scaling
        
        # Entity attributes - name already includes host for uniqueness
        self._attr_name = name
        self._attr_unique_id = f"midea_{config['host']}_{config[CONF_MODBUS_UNIT]}_{sensor_id}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def device_info(self):
        """Return device info to link this sensor to the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config['host']}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config['host']})",
            "manufacturer": "Midea",
            "model": "Heat Pump Water Heater",
        }

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        if self.coordinator.data:
            # Get the value from coordinator data
            return self.coordinator.data.get(self._sensor_id)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._sensor_id in (self.coordinator.data or {})

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()