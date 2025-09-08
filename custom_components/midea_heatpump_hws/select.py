"""Support for Midea Heat Pump mode selection."""
import logging
import asyncio
from pymodbus.client import AsyncModbusTcpClient

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_MODBUS_UNIT,
    CONF_SCAN_INTERVAL,
    CONF_MODE_REGISTER,
    CONF_ECO_MODE_VALUE,
    CONF_PERFORMANCE_MODE_VALUE,
    CONF_ELECTRIC_MODE_VALUE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea mode selector from config entry."""
    config = config_entry.data
    
    entities = [MideaModeSelect(config)]
    async_add_entities(entities)


class MideaModeSelect(SelectEntity):
    """Representation of mode selector."""

    def __init__(self, config: dict):
        """Initialize the mode selector."""
        self._offline_mode = True  # Set to False for production
        self._config = config
        
        # Entity attributes
        self._attr_name = "Operation Mode"
        self._attr_unique_id = f"midea_{config[CONF_HOST]}_{config[CONF_MODBUS_UNIT]}_mode_select"
        self._attr_icon = "mdi:cog"
        
        # Mode mapping
        self._mode_values = {
            "eco": config[CONF_ECO_MODE_VALUE],
            "performance": config[CONF_PERFORMANCE_MODE_VALUE], 
            "electric": config[CONF_ELECTRIC_MODE_VALUE]
        }
        self._value_to_mode = {v: k for k, v in self._mode_values.items()}
        
        self._attr_options = ["eco", "performance", "electric"]
        self._attr_current_option = "eco"
        
        # Connection settings
        self._host = config[CONF_HOST]
        self._port = config[CONF_PORT]
        self._modbus_unit = config[CONF_MODBUS_UNIT]
        self._scan_interval = config[CONF_SCAN_INTERVAL]
        self._mode_register = config[CONF_MODE_REGISTER]
        
        # State
        self._client = None
        self._update_task = None
        self._attr_available = False
        self._attr_should_poll = False

    @property
    def device_info(self):
        """Return device info to link this selector to the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config[CONF_HOST]}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config[CONF_HOST]})",
            "manufacturer": "Midea",
            "model": "Heat Pump Water Heater",
        }

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
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
        """Read mode from modbus."""
        try:
            if not self._client.connected:
                await self._client.connect()
            
            result = await self._client.read_holding_registers(
                address=self._mode_register,
                count=1,
                slave=self._modbus_unit
            )
            
            if not result.isError():
                mode_value = result.registers[0]
                self._attr_current_option = self._value_to_mode.get(mode_value, "eco")
                self._attr_available = True
            else:
                self._attr_available = False
                
        except Exception as ex:
            _LOGGER.warning("Cannot connect to %s, will retry: %s", self._attr_name, ex)
            self._attr_available = False
        
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self._attr_options:
            return
            
        try:
            if not self._client.connected:
                await self._client.connect()
            
            mode_value = self._mode_values[option]
            result = await self._client.write_register(
                address=self._mode_register,
                value=mode_value,
                slave=self._modbus_unit
            )
            
            if not result.isError():
                self._attr_current_option = option
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to set mode for %s", self._attr_name)
                
        except Exception as ex:
            _LOGGER.error("Error setting mode for %s: %s", self._attr_name, ex)