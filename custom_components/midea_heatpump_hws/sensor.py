"""Support for Midea Heat Pump temperature sensors."""
import logging
import asyncio
from pymodbus.client import AsyncModbusTcpClient

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_MODBUS_UNIT,
    CONF_SCAN_INTERVAL,
    CONF_TEMP_REGISTER,
    CONF_TARGET_TEMP_REGISTER,
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea temperature sensors from config entry."""
    config = config_entry.data
    
    entities = []
    
    # Main temperature sensor
    entities.append(
        MideaTemperatureSensor(
            config,
            "current_temp",
            "Current Temperature",
            config[CONF_TEMP_REGISTER],
            use_scaling=True
        )
    )
    
    # Target temperature sensor (read-only)
    entities.append(
        MideaTemperatureSensor(
            config,
            "target_temp",
            "Target Temperature",
            config[CONF_TARGET_TEMP_REGISTER],
            use_scaling=False
        )
    )
    
    # Additional temperature sensors if enabled
    if config.get(CONF_ENABLE_ADDITIONAL_SENSORS, True):
        sensor_configs = [
            ("tank_top_temp", "Tank Top Temperature", config.get(CONF_TANK_TOP_TEMP_REGISTER), True),
            ("tank_bottom_temp", "Tank Bottom Temperature", config.get(CONF_TANK_BOTTOM_TEMP_REGISTER), True),
            ("condensor_temp", "Condensor Temperature", config.get(CONF_CONDENSOR_TEMP_REGISTER), False),
            ("outdoor_temp", "Outdoor Temperature", config.get(CONF_OUTDOOR_TEMP_REGISTER), False),
            ("exhaust_temp", "Exhaust Gas Temperature", config.get(CONF_EXHAUST_TEMP_REGISTER), False),
            ("suction_temp", "Suction Temperature", config.get(CONF_SUCTION_TEMP_REGISTER), False),
        ]
        
        for sensor_id, name, register, use_scaling in sensor_configs:
            if register is not None:
                entities.append(
                    MideaTemperatureSensor(config, sensor_id, name, register, use_scaling)
                )
    
    async_add_entities(entities)


class MideaTemperatureSensor(SensorEntity):
    """Representation of a Midea temperature sensor."""

    def __init__(self, config: dict, sensor_id: str, name: str, register: int, use_scaling: bool):
        """Initialize the temperature sensor."""
        self._config = config
        self._sensor_id = sensor_id
        self._register = register
        self._use_scaling = use_scaling
        
        # Entity attributes
        self._attr_name = name
        self._attr_unique_id = f"midea_{config[CONF_HOST]}_{config[CONF_MODBUS_UNIT]}_{sensor_id}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        
        # Connection settings
        self._host = config[CONF_HOST]
        self._port = config[CONF_PORT]
        self._modbus_unit = config[CONF_MODBUS_UNIT]
        self._scan_interval = config[CONF_SCAN_INTERVAL]
        
        # Temperature scaling
        self._temp_offset = config[CONF_TEMP_OFFSET] if use_scaling else 0
        self._temp_scale = config[CONF_TEMP_SCALE] if use_scaling else 1
        
        # State
        self._attr_native_value = None
        self._client = None
        self._update_task = None
        self._attr_available = False
        self._attr_should_poll = False

    @property
    def device_info(self):
        """Return device info to link this sensor to the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config[CONF_HOST]}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config[CONF_HOST]})",
            "manufacturer": "Midea",
            "model": "Heat Pump Water Heater",
        }

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        
        # Initialize modbus client
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        
        # Start polling
        await self._start_polling()

    async def async_will_remove_from_hass(self):
        """Run when entity will be removed."""
        await self._stop_polling()
        if self._client and self._client.connected:
            self._client.close()

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
        """Read temperature from modbus."""
        try:
            if not self._client.connected:
                await self._client.connect()
            
            result = await self._client.read_holding_registers(
                address=self._register,
                count=1,
                slave=self._modbus_unit
            )
            
            if not result.isError():
                raw_value = result.registers[0]
                
                if self._use_scaling:
                    self._attr_native_value = (raw_value * self._temp_scale) + self._temp_offset
                else:
                    self._attr_native_value = raw_value
                
                self._attr_available = True
            else:
                self._attr_available = False
                
        except Exception as ex:
            _LOGGER.error("Error reading %s: %s", self._attr_name, ex)
            self._attr_available = False
        
        self.async_write_ha_state()