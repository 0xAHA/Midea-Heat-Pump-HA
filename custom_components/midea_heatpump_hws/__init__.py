"""The Midea Heat Pump Water Heater integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN
from .coordinator import MideaModbusCoordinator
from .profile_manager import ProfileManager

_LOGGER = logging.getLogger(__name__)

# Define platforms here directly to avoid import issues
PLATFORMS: list[Platform] = [
    Platform.WATER_HEATER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]

# Service schemas
SERVICE_EXPORT_PROFILE = "export_profile"
SERVICE_IMPORT_PROFILE = "import_profile"

EXPORT_PROFILE_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Optional("name", default="My Profile"): cv.string,
    vol.Optional("model", default="Custom"): cv.string,
})

IMPORT_PROFILE_SCHEMA = vol.Schema({
    vol.Required("profile_json"): cv.string,
})


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

    # Register services (only once, not per entry)
    if not hass.services.has_service(DOMAIN, SERVICE_EXPORT_PROFILE):
        await _register_services(hass)

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
        
        # Remove services if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_EXPORT_PROFILE)
            hass.services.async_remove(DOMAIN, SERVICE_IMPORT_PROFILE)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Reload the integration
    await hass.config_entries.async_reload(entry.entry_id)


async def _register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    
    async def handle_export_profile(call: ServiceCall) -> None:
        """Handle profile export service call."""
        # Get the entry to export
        entry_id = call.data.get("entry_id")
        if entry_id:
            if entry_id not in hass.data[DOMAIN]:
                _LOGGER.error("Invalid entry_id: %s", entry_id)
                return
        else:
            # Use first entry if not specified
            if not hass.data[DOMAIN]:
                _LOGGER.error("No configured entries to export")
                return
            entry_id = list(hass.data[DOMAIN].keys())[0]
        
        config = hass.data[DOMAIN][entry_id]["config"]
        
        # Create profile
        profile_manager = ProfileManager(hass)
        profile_data = {
            "name": call.data.get("name", config.get("name", "My Profile")),
            "model": call.data.get("model", "Custom"),
            "exported": datetime.now().isoformat(),
            "version": "0.2.2",
            "integration": "midea_heatpump_hws",
            "connection": {
                "port": config.get("port", 502),
                "modbus_unit": config.get("modbus_unit", 1),
                "scan_interval": config.get("scan_interval", 60)
            },
            "registers": {
                "power": config.get("power_register", 0),
                "mode": config.get("mode_register", 1),
                "current_temp": config.get("temp_register", 102),
                "target_temp": config.get("target_temp_register", 2),
                "tank_top_temp": config.get("tank_top_temp_register", 101),
                "tank_bottom_temp": config.get("tank_bottom_temp_register", 102),
                "condensor_temp": config.get("condensor_temp_register", 103),
                "outdoor_temp": config.get("outdoor_temp_register", 104),
                "exhaust_temp": config.get("exhaust_temp_register", 105),
                "suction_temp": config.get("suction_temp_register", 106)
            },
            "mode_values": {
                "eco": config.get("eco_mode_value", 1),
                "performance": config.get("performance_mode_value", 2),
                "electric": config.get("electric_mode_value", 4)
            },
            "scaling": {
                "current_temp": {
                    "offset": config.get("temp_offset", -15.0),
                    "scale": config.get("temp_scale", 0.5)
                },
                "target_temp": {
                    "offset": config.get("target_temp_offset", 0.0),
                    "scale": config.get("target_temp_scale", 1.0)
                },
                "sensors": {
                    "offset": config.get("sensors_temp_offset", -15.0),
                    "scale": config.get("sensors_temp_scale", 0.5)
                }
            },
            "temp_limits": {
                "eco": {
                    "min": config.get("eco_min_temp", 60),
                    "max": config.get("eco_max_temp", 65)
                },
                "performance": {
                    "min": config.get("performance_min_temp", 60),
                    "max": config.get("performance_max_temp", 70)
                },
                "electric": {
                    "min": config.get("electric_min_temp", 60),
                    "max": config.get("electric_max_temp", 70)
                }
            },
            "defaults": {
                "target_temperature": config.get("target_temperature", 65),
                "enable_additional_sensors": config.get("enable_additional_sensors", True)
            }
        }
        
        # Save to www folder for download
        www_path = hass.config.path("www")
        if not Path(www_path).exists():
            Path(www_path).mkdir()
        
        # Create filename
        safe_name = call.data.get("name", "profile").lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        filename = f"midea_profile_{safe_name}_{datetime.now():%Y%m%d_%H%M%S}.json"
        file_path = Path(www_path) / filename
        
        # Write file
        with open(file_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Create persistent notification with download link
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "🎉 Profile Exported Successfully!",
                "message": (
                    f"Your water heater configuration has been exported.\n\n"
                    f"**[📥 Download Profile](/local/{filename})**\n\n"
                    f"**→ Right-click the link above and select 'Save Link As...' to download**\n\n"
                    f"Share this profile with others using the same model, "
                    f"or keep it as a backup of your configuration."
                ),
                "notification_id": f"midea_profile_export_{datetime.now():%Y%m%d%H%M%S}"
            }
        )
        
        _LOGGER.info("Profile exported to %s", file_path)
    
    async def handle_import_profile(call: ServiceCall) -> None:
        """Handle profile import service call."""
        try:
            profile_json = call.data.get("profile_json")
            profile_data = json.loads(profile_json)
            
            # Save as custom profile
            profile_manager = ProfileManager(hass)
            saved_path = profile_manager.import_profile(profile_data)
            
            if saved_path:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "✅ Profile Imported",
                        "message": (
                            f"Profile '{profile_data.get('name', 'Imported')}' has been imported successfully.\n\n"
                            f"You can now use it when adding a new water heater."
                        ),
                        "notification_id": f"midea_profile_import_{datetime.now():%Y%m%d%H%M%S}"
                    }
                )
                _LOGGER.info("Profile imported successfully: %s", saved_path)
            else:
                _LOGGER.error("Failed to import profile")
                
        except json.JSONDecodeError as e:
            _LOGGER.error("Invalid JSON in profile import: %s", e)
        except Exception as e:
            _LOGGER.error("Error importing profile: %s", e)
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_PROFILE,
        handle_export_profile,
        schema=EXPORT_PROFILE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_PROFILE,
        handle_import_profile,
        schema=IMPORT_PROFILE_SCHEMA,
    )