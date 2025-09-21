"""Profile management for Midea Heat Pump Water Heater integration."""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PROFILE_DIR = Path(__file__).parent / "models"
DEFAULT_PROFILES_DIR = PROFILE_DIR / "defaults"
CUSTOM_PROFILES_DIR = PROFILE_DIR / "custom"


class ProfileManager:
    """Manage device profiles for the integration."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the profile manager."""
        self.hass = hass
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure profile directories exist."""
        DEFAULT_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_available_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all available profiles."""
        profiles = {}
        
        # Load built-in profiles
        for profile_file in DEFAULT_PROFILES_DIR.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profile_id = f"default_{profile_file.stem}"
                    profiles[profile_id] = {
                        "name": data.get("name", profile_file.stem),
                        "model": data.get("model", "Unknown"),
                        "type": "built-in",
                        "path": str(profile_file),
                        "data": data
                    }
            except Exception as e:
                _LOGGER.error("Failed to load profile %s: %s", profile_file, e)
        
        # Load custom profiles
        for profile_file in CUSTOM_PROFILES_DIR.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profile_id = f"custom_{profile_file.stem}"
                    profiles[profile_id] = {
                        "name": data.get("name", profile_file.stem),
                        "model": data.get("model", "Custom"),
                        "type": "custom",
                        "path": str(profile_file),
                        "created": data.get("created", "Unknown"),
                        "data": data
                    }
            except Exception as e:
                _LOGGER.error("Failed to load profile %s: %s", profile_file, e)
        
        return profiles
    
    def load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific profile."""
        profiles = self.get_available_profiles()
        if profile_id in profiles:
            return profiles[profile_id]["data"]
        return None
    
    def save_profile(self, name: str, config: Dict[str, Any], model: str = "Custom") -> str:
        """Save current configuration as a profile."""
        # Sanitize filename
        safe_name = re.sub(r'[^\w\s-]', '', name).strip().lower()
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        
        # Create profile data
        profile_data = {
            "name": name,
            "model": model,
            "manufacturer": config.get("manufacturer", "Unknown"),
            "version": "1.0",
            "description": f"Custom profile for {name}",
            "created": datetime.now().isoformat(),
            "author": "User Created",
            
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
        
        # Save to file
        profile_path = CUSTOM_PROFILES_DIR / f"{safe_name}.json"
        
        # Check if file exists and add number if needed
        counter = 1
        while profile_path.exists():
            profile_path = CUSTOM_PROFILES_DIR / f"{safe_name}_{counter}.json"
            counter += 1
        
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        _LOGGER.info("Saved profile %s to %s", name, profile_path)
        return str(profile_path)
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a custom profile."""
        if not profile_id.startswith("custom_"):
            _LOGGER.error("Cannot delete built-in profiles")
            return False
        
        profiles = self.get_available_profiles()
        if profile_id in profiles:
            profile_path = Path(profiles[profile_id]["path"])
            try:
                profile_path.unlink()
                _LOGGER.info("Deleted profile %s", profile_path)
                return True
            except Exception as e:
                _LOGGER.error("Failed to delete profile: %s", e)
        
        return False
    
    def export_profile(self, config: Dict[str, Any], name: str = None) -> Dict[str, Any]:
        """Export configuration as a shareable profile."""
        if name is None:
            name = config.get("name", "Exported Profile")
        
        return {
            "name": name,
            "model": config.get("model", "Unknown"),
            "exported": datetime.now().isoformat(),
            "version": "0.2.2",
            "integration": "midea_heatpump_hws",
            "config": config
        }
    
    def import_profile(self, profile_data: Dict[str, Any]) -> Optional[str]:
        """Import a profile from exported data."""
        try:
            # Validate profile data
            if "config" not in profile_data:
                _LOGGER.error("Invalid profile data: missing config")
                return None
            
            name = profile_data.get("name", "Imported Profile")
            model = profile_data.get("model", "Unknown")
            config = profile_data["config"]
            
            # Save as custom profile
            return self.save_profile(name, config, model)
            
        except Exception as e:
            _LOGGER.error("Failed to import profile: %s", e)
            return None
    
    def apply_profile_to_config(self, profile_data: Dict[str, Any], user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Apply profile data to configuration, keeping user's connection settings."""
        config = {}
        
        # Keep user's connection settings
        config["host"] = user_input.get("host")
        config["port"] = profile_data.get("connection", {}).get("port", 502)
        config["modbus_unit"] = profile_data.get("connection", {}).get("modbus_unit", 1)
        config["scan_interval"] = profile_data.get("connection", {}).get("scan_interval", 60)
        
        # Apply register settings from profile
        registers = profile_data.get("registers", {})
        config["power_register"] = registers.get("power", 0)
        config["mode_register"] = registers.get("mode", 1)
        config["temp_register"] = registers.get("current_temp", 102)
        config["target_temp_register"] = registers.get("target_temp", 2)
        config["tank_top_temp_register"] = registers.get("tank_top_temp", 101)
        config["tank_bottom_temp_register"] = registers.get("tank_bottom_temp", 102)
        config["condensor_temp_register"] = registers.get("condensor_temp", 103)
        config["outdoor_temp_register"] = registers.get("outdoor_temp", 104)
        config["exhaust_temp_register"] = registers.get("exhaust_temp", 105)
        config["suction_temp_register"] = registers.get("suction_temp", 106)
        
        # Apply mode values
        mode_values = profile_data.get("mode_values", {})
        config["eco_mode_value"] = mode_values.get("eco", 1)
        config["performance_mode_value"] = mode_values.get("performance", 2)
        config["electric_mode_value"] = mode_values.get("electric", 4)
        
        # Apply scaling
        scaling = profile_data.get("scaling", {})
        if "current_temp" in scaling:
            config["temp_offset"] = scaling["current_temp"].get("offset", -15.0)
            config["temp_scale"] = scaling["current_temp"].get("scale", 0.5)
        if "target_temp" in scaling:
            config["target_temp_offset"] = scaling["target_temp"].get("offset", 0.0)
            config["target_temp_scale"] = scaling["target_temp"].get("scale", 1.0)
        if "sensors" in scaling:
            config["sensors_temp_offset"] = scaling["sensors"].get("offset", -15.0)
            config["sensors_temp_scale"] = scaling["sensors"].get("scale", 0.5)
        
        # Apply temperature limits
        temp_limits = profile_data.get("temp_limits", {})
        if "eco" in temp_limits:
            config["eco_min_temp"] = temp_limits["eco"].get("min", 60)
            config["eco_max_temp"] = temp_limits["eco"].get("max", 65)
        if "performance" in temp_limits:
            config["performance_min_temp"] = temp_limits["performance"].get("min", 60)
            config["performance_max_temp"] = temp_limits["performance"].get("max", 70)
        if "electric" in temp_limits:
            config["electric_min_temp"] = temp_limits["electric"].get("min", 60)
            config["electric_max_temp"] = temp_limits["electric"].get("max", 70)
        
        # Apply defaults
        defaults = profile_data.get("defaults", {})
        config["target_temperature"] = defaults.get("target_temperature", 65)
        config["enable_additional_sensors"] = defaults.get("enable_additional_sensors", True)
        
        # Apply user's entity name if provided
        config["name"] = user_input.get("name", profile_data.get("name", "Hot Water System"))
        
        return config