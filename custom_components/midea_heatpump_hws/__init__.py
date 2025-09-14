"""The Midea Heat Pump Water Heater integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MideaModbusCoordinator

_LOGGER = logging.getLogger(__name__)

# Define platforms here directly to avoid import issues
PLATFORMS: list[Platform] = [
    Platform.WATER_HEATER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Midea Heat Pump Water Heater from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create the coordinator
    coordinator = MideaModbusCoordinator(hass, entry.data)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator and config
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Setup update listener for options flow
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up coordinator
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        await coordinator.async_shutdown()
        
        # Remove from data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Reload the integration
    await hass.config_entries.async_reload(entry.entry_id)