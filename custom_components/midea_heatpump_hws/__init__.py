"""The midea_water_heater integration."""
import logging

import voluptuous as vol

from homeassistant.components.water_heater import DOMAIN as WATER_HEATER_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "midea_heatpump_hws"

# Old constants (keep for compatibility)
CONF_HEATER = "heater_switch"
CONF_SENSOR = "temperature_sensor"
CONF_TARGET_TEMP = "target_temperature"
CONF_TEMP_DELTA = "delta_temperature"
CONF_TEMP_MIN = "min_temp"
CONF_TEMP_MAX = "max_temp"

# New modbus constants
CONF_MODBUS_HOST = "modbus_host"
CONF_MODBUS_PORT = "modbus_port"
CONF_MODBUS_UNIT = "modbus_unit"          # ← This one is missing!
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TEMP_REGISTER = "temp_register"
CONF_TARGET_TEMP_REGISTER = "target_temp_register"
CONF_MODE_REGISTER = "mode_register"
CONF_POWER_REGISTER = "power_register"
CONF_TEMP_OFFSET = "temp_offset"
CONF_TEMP_SCALE = "temp_scale"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        cv.slug: vol.Schema({
            vol.Optional("friendly_name"): cv.string,
            # Modbus connection
            vol.Required(CONF_MODBUS_HOST): cv.string,
            vol.Optional(CONF_MODBUS_PORT, default=502): vol.Coerce(int),
            vol.Optional(CONF_MODBUS_UNIT, default=1): vol.Coerce(int),
            vol.Optional(CONF_SCAN_INTERVAL, default=30): vol.Coerce(int),
            
            # Register addresses  
            vol.Required(CONF_TEMP_REGISTER): vol.Coerce(int),
            vol.Required(CONF_TARGET_TEMP_REGISTER): vol.Coerce(int),
            vol.Required(CONF_MODE_REGISTER): vol.Coerce(int),
            vol.Required(CONF_POWER_REGISTER): vol.Coerce(int),
            
            # Temperature scaling
            vol.Optional(CONF_TEMP_OFFSET, default=0): vol.Coerce(float),
            vol.Optional(CONF_TEMP_SCALE, default=1): vol.Coerce(float),
            
            # Temperature limits
            vol.Optional(CONF_TARGET_TEMP, default=65): vol.Coerce(float),
            vol.Optional(CONF_TEMP_MIN, default=40): vol.Coerce(float),
            vol.Optional(CONF_TEMP_MAX, default=75): vol.Coerce(float),
        })
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, hass_config):
    """Set up Generic Water Heaters."""
    for water_heater, conf in hass_config.get(DOMAIN).items():
        _LOGGER.debug("Setup %s.%s", DOMAIN, water_heater)

        conf[CONF_NAME] = water_heater
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                WATER_HEATER_DOMAIN,
                DOMAIN,
                [conf],
                hass_config,
            )
        )
    return True
