"""The midea_water_heater integration."""
import logging

import voluptuous as vol

from homeassistant.components.water_heater import DOMAIN as WATER_HEATER_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "midea_heatpump_hws"

CONF_HEATER = "heater_switch"
CONF_SENSOR = "temperature_sensor"
CONF_TARGET_TEMP = "target_temperature"
CONF_TEMP_DELTA = "delta_temperature"
CONF_TEMP_MIN = "min_temp"
CONF_TEMP_MAX = "max_temp"
CONF_MODE_SENSOR = "mode_sensor"    
CONF_MODBUS_HUB = "modbus_hub"  
CONF_MODBUS_UNIT = "modbus_unit" 
CONF_TARGET_TEMP_REGISTER = "target_temp_register"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                cv.slug: vol.Schema(
                    {
                        vol.Required(CONF_HEATER): cv.entity_id,
                        vol.Required(CONF_SENSOR): cv.entity_id,
                        vol.Required(CONF_MODE_SENSOR): cv.entity_id,
                        vol.Optional(CONF_TEMP_DELTA): vol.Coerce(float),
                        vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
                        vol.Optional(CONF_TEMP_MIN): vol.Coerce(float),
                        vol.Optional(CONF_TEMP_MAX): vol.Coerce(float),
                        vol.Optional(CONF_MODBUS_HUB): cv.string,        
                        vol.Optional(CONF_MODBUS_UNIT, default=1): vol.Coerce(int), 
                        vol.Optional(CONF_TARGET_TEMP_REGISTER, default=2): vol.Coerce(int),  
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


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
