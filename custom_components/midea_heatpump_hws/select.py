"""Support for Midea Heat Pump mode selection."""
import logging

from homeassistant.components.select import SelectEntity
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
    """Set up Midea mode selector from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]
    
    entities = [MideaModeSelect(coordinator, config)]
    async_add_entities(entities)


class MideaModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of mode selector."""

    def __init__(
        self,
        coordinator: MideaModbusCoordinator,
        config: dict
    ):
        """Initialize the mode selector."""
        super().__init__(coordinator)
        self._config = config
        
        # Entity attributes
        self._attr_name = "Operation Mode"
        self._attr_unique_id = f"midea_{config['host']}_{config[CONF_MODBUS_UNIT]}_mode_select"
        self._attr_icon = "mdi:cog"
        self._attr_options = ["eco", "performance", "electric"]

    @property
    def device_info(self):
        """Return device info to link this selector to the main device."""
        return {
            "identifiers": {(DOMAIN, f"{self._config['host']}_{self._config[CONF_MODBUS_UNIT]}")},
            "name": f"Midea Heat Pump ({self._config['host']})",
            "manufacturer": "0xAHA",
            "model": "Heat Pump Water Heater",
        }

    @property
    def current_option(self):
        """Return the selected entity option."""
        if self.coordinator.data:
            return self.coordinator.data.get("mode", "Eco")
        return "Eco"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in self._attr_options:
            await self.coordinator.write_register("mode", option)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()