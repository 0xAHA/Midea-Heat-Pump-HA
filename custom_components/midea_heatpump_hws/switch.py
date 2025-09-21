"""Support for Midea Heat Pump power switch."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_MODBUS_UNIT
from .coordinator import MideaModbusCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Midea switches from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]
    
    # Include host in entity name to make it unique
    host_suffix = f" ({config['host']})"
    
    # Only create power switch
    entities = [MideaPowerSwitch(coordinator, config, host_suffix)]
    async_add_entities(entities)


class MideaPowerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the main power switch."""

    def __init__(
        self,
        coordinator: MideaModbusCoordinator,
        config: dict,
        host_suffix: str
    ):
        """Initialize the power switch."""
        super().__init__(coordinator)
        self._config = config
        
        # Entity attributes - include host for uniqueness
        self._attr_name = f"Power{host_suffix}"
        self._attr_unique_id = f"midea_{config['host']}_{config[CONF_MODBUS_UNIT]}_power"
        self._attr_icon = "mdi:power"

    @property
    def device_info(self):
        """Return device info to link this switch to the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config['host']}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config['host']})",
            "manufacturer": "Midea",
            "model": "Heat Pump Water Heater",
        }

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if self.coordinator.data:
            return self.coordinator.data.get("power_state", False)
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.write_register("power_state", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.write_register("power_state", False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()