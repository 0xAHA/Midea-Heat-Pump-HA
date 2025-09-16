"""Config flow for Midea Heat Pump Water Heater integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Step 1: Connection settings
STEP_CONNECTION_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST, default="192.168.1.60"): str,
    vol.Required(CONF_PORT, default=502): int,
    vol.Required("modbus_unit", default=1): int,
    vol.Required("scan_interval", default=60): int,
})

# Step 2: Control registers (no scaling needed)
STEP_CONTROL_REGISTERS_SCHEMA = vol.Schema({
    vol.Required("power_register", default=0): int,
    vol.Required("mode_register", default=1): int,
    vol.Required("eco_mode_value", default=1): int,
    vol.Required("performance_mode_value", default=2): int,
    vol.Required("electric_mode_value", default=4): int,
})

# Step 3: Temperature registers with individual scaling
STEP_TEMP_REGISTERS_SCHEMA = vol.Schema({
    vol.Required("temp_register", default=102): int,
    vol.Required("temp_offset", default=-15.0): vol.Coerce(float),
    vol.Required("temp_scale", default=0.5): vol.Coerce(float),
    vol.Required("target_temp_register", default=2): int,
    vol.Required("target_temp_offset", default=0.0): vol.Coerce(float),
    vol.Required("target_temp_scale", default=1.0): vol.Coerce(float),
})

# Step 4: Temperature limits by mode
STEP_TEMP_LIMITS_SCHEMA = vol.Schema({
    # Eco mode limits
    vol.Required("eco_min_temp", default=60): vol.All(int, vol.Range(min=40, max=80)),
    vol.Required("eco_max_temp", default=65): vol.All(int, vol.Range(min=40, max=80)),
    # Performance mode limits
    vol.Required("performance_min_temp", default=60): vol.All(int, vol.Range(min=40, max=80)),
    vol.Required("performance_max_temp", default=70): vol.All(int, vol.Range(min=40, max=80)),
    # Electric mode limits
    vol.Required("electric_min_temp", default=60): vol.All(int, vol.Range(min=40, max=80)),
    vol.Required("electric_max_temp", default=70): vol.All(int, vol.Range(min=40, max=80)),
})

# Step 5: Optional sensors with shared scaling
STEP_SENSORS_DATA_SCHEMA = vol.Schema({
    vol.Optional("tank_top_temp_register", default=101): int,
    vol.Optional("tank_bottom_temp_register", default=102): int,
    vol.Optional("condensor_temp_register", default=103): int,
    vol.Optional("outdoor_temp_register", default=104): int,
    vol.Optional("exhaust_temp_register", default=105): int,
    vol.Optional("suction_temp_register", default=106): int,
    vol.Optional("enable_additional_sensors", default=True): bool,
    vol.Optional("sensors_temp_offset", default=-15.0): vol.Coerce(float),
    vol.Optional("sensors_temp_scale", default=0.5): vol.Coerce(float),
})

# Step 6: Final settings
STEP_FINAL_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME, default="Hot Water System"): str,
    vol.Required("target_temperature", default=65): int,
})


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the modbus connection with retry logic."""
    
    # Skip validation if requested
    if data.get("skip_validation", False):
        _LOGGER.info("Skipping connection validation as requested")
        return {"title": f"Midea Heat Pump ({data[CONF_HOST]})"}
    
    client = None
    max_retries = 3
    
    for attempt in range(max_retries):
        client = AsyncModbusTcpClient(host=data[CONF_HOST], port=data[CONF_PORT])
        
        try:
            # Connect with timeout
            connect_result = await client.connect()
            if not client.connected:
                if attempt < max_retries - 1:
                    _LOGGER.warning("Connection attempt %d failed, retrying...", attempt + 1)
                    if client:
                        client.close()
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception("Unable to connect to modbus device after 3 attempts")
            
            # Try to read a register to verify communication
            result = await client.read_holding_registers(
                address=data.get("mode_register", 1),
                count=1,
                device_id=data.get("modbus_unit", 1)
            )
            
            if result.isError():
                if attempt < max_retries - 1:
                    _LOGGER.warning("Read attempt %d failed, retrying...", attempt + 1)
                    client.close()
                    await asyncio.sleep(1)
                    continue
                else:
                    raise Exception("Unable to read from modbus device after 3 attempts")
            
            # Success!
            client.close()
            
            # Return info that you want to store in the config entry
            return {"title": f"Midea Heat Pump ({data[CONF_HOST]})"}
            
        except ModbusException as ex:
            if attempt < max_retries - 1:
                _LOGGER.warning("Modbus error on attempt %d: %s, retrying...", attempt + 1, ex)
                if client:
                    client.close()
                await asyncio.sleep(1)
                continue
            else:
                raise Exception(f"Modbus error after 3 attempts: {ex}")
        except Exception as ex:
            if attempt < max_retries - 1:
                _LOGGER.warning("Connection error on attempt %d: %s, retrying...", attempt + 1, ex)
                if client:
                    client.close()
                await asyncio.sleep(1)
                continue
            else:
                raise Exception(f"Connection failed after 3 attempts: {ex}")
    
    # This shouldn't be reached, but just in case
    raise Exception("Connection validation failed")


class MideaHeatPumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Midea Heat Pump Water Heater."""

    VERSION = 1

    def __init__(self):
        """Initialize config flow."""
        self.data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MideaHeatPumpOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - Modbus connection settings."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_CONNECTION_DATA_SCHEMA,
                description_placeholders={
                    "title": "Modbus Connection Settings",
                    "description": "Configure the TCP connection to your EW11-A adapter"
                },
            )

        errors = {}

        # TEMPORARILY BYPASS VALIDATION FOR TESTING
        try:
            # Comment out the actual validation for testing
            # info = await validate_connection(self.hass, user_input)
            
            # Use fake validation result for offline testing
            info = {"title": f"Midea Heat Pump ({user_input[CONF_HOST]})"}
            
        except Exception as ex:
            _LOGGER.exception("Unexpected exception: %s", ex)
            errors["base"] = "cannot_connect"
        else:
            self.data.update(user_input)
            self.data["title"] = info["title"]
            return await self.async_step_registers()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_CONNECTION_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "title": "Modbus Connection Settings",
                "description": "Configure the TCP connection to your EW11-A adapter"
            },
        )

    async def async_step_registers(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the second step - control register configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="registers",
                data_schema=STEP_CONTROL_REGISTERS_SCHEMA,
                description_placeholders={
                    "title": "Control Register Configuration",
                    "description": "Configure power and mode register addresses (no scaling needed)"
                },
            )

        self.data.update(user_input)
        return await self.async_step_temp_registers()

    async def async_step_temp_registers(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle temperature register configuration with scaling."""
        if user_input is None:
            return self.async_show_form(
                step_id="temp_registers",
                data_schema=STEP_TEMP_REGISTERS_SCHEMA,
                description_placeholders={
                    "title": "Temperature Register Configuration",
                    "description": "Configure temperature registers with individual offset and scale values"
                },
            )

        self.data.update(user_input)
        return await self.async_step_temp_limits()

    async def async_step_temp_limits(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle temperature limits by mode configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="temp_limits",
                data_schema=STEP_TEMP_LIMITS_SCHEMA,
                description_placeholders={
                    "title": "Temperature Limits by Mode",
                    "description": "Configure min/max temperatures for each operation mode"
                },
            )

        self.data.update(user_input)
        return await self.async_step_sensors()

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the optional sensor configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="sensors",
                data_schema=STEP_SENSORS_DATA_SCHEMA,
                description_placeholders={
                    "title": "Optional Sensors",
                    "description": "Configure additional temperature sensors with shared scaling"
                },
            )

        self.data.update(user_input)
        return await self.async_step_final()

    async def async_step_final(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the final step - entity settings."""
        if user_input is None:
            return self.async_show_form(
                step_id="final",
                data_schema=STEP_FINAL_DATA_SCHEMA,
                description_placeholders={
                    "title": "Entity Settings",
                    "description": "Configure entity name and default temperature"
                },
            )

        self.data.update(user_input)

        # Check if already configured
        await self.async_set_unique_id(f"{self.data[CONF_HOST]}_{self.data['modbus_unit']}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=self.data["title"],
            data=self.data,
        )


class MideaHeatPumpOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Midea Heat Pump."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.data = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options - show menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["connection", "control_registers", "temp_registers", "temp_limits", "sensors", "settings"]
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update connection settings."""
        if user_input is not None:
            self.data.update(user_input)
            return await self._update_and_reload()

        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="connection",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=current_data.get(CONF_HOST)): str,
                vol.Required(CONF_PORT, default=current_data.get(CONF_PORT, 502)): int,
                vol.Required("modbus_unit", default=current_data.get("modbus_unit", 1)): int,
                vol.Required("scan_interval", default=current_data.get("scan_interval", 60)): vol.All(
                    int, vol.Range(min=30, max=300)
                ),
            }),
            description_placeholders={
                "title": "Update Connection Settings",
                "description": "Modify Modbus connection parameters"
            },
        )

    async def async_step_control_registers(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update control register settings (no scaling)."""
        if user_input is not None:
            self.data.update(user_input)
            return await self._update_and_reload()

        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="control_registers",
            data_schema=vol.Schema({
                vol.Required("power_register", default=current_data.get("power_register", 0)): int,
                vol.Required("mode_register", default=current_data.get("mode_register", 1)): int,
                vol.Required("eco_mode_value", default=current_data.get("eco_mode_value", 1)): int,
                vol.Required("performance_mode_value", default=current_data.get("performance_mode_value", 2)): int,
                vol.Required("electric_mode_value", default=current_data.get("electric_mode_value", 4)): int,
            }),
            description_placeholders={
                "title": "Update Control Registers",
                "description": "Modify power and mode register addresses (no scaling needed)"
            },
        )

    async def async_step_temp_registers(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update temperature register settings with individual scaling."""
        if user_input is not None:
            self.data.update(user_input)
            return await self._update_and_reload()

        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="temp_registers",
            data_schema=vol.Schema({
                vol.Required("temp_register", default=current_data.get("temp_register", 102)): int,
                vol.Required("temp_offset", default=current_data.get("temp_offset", -15.0)): vol.Coerce(float),
                vol.Required("temp_scale", default=current_data.get("temp_scale", 0.5)): vol.Coerce(float),
                vol.Required("target_temp_register", default=current_data.get("target_temp_register", 2)): int,
                vol.Required("target_temp_offset", default=current_data.get("target_temp_offset", 0.0)): vol.Coerce(float),
                vol.Required("target_temp_scale", default=current_data.get("target_temp_scale", 1.0)): vol.Coerce(float),
            }),
            description_placeholders={
                "title": "Update Temperature Registers",
                "description": "Configure temperature registers with individual offset and scale values"
            },
        )

    async def async_step_temp_limits(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update temperature limits by mode."""
        if user_input is not None:
            self.data.update(user_input)
            return await self._update_and_reload()

        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="temp_limits",
            data_schema=vol.Schema({
                vol.Required("eco_min_temp", default=current_data.get("eco_min_temp", 60)): vol.All(
                    int, vol.Range(min=40, max=80)
                ),
                vol.Required("eco_max_temp", default=current_data.get("eco_max_temp", 65)): vol.All(
                    int, vol.Range(min=40, max=80)
                ),
                vol.Required("performance_min_temp", default=current_data.get("performance_min_temp", 60)): vol.All(
                    int, vol.Range(min=40, max=80)
                ),
                vol.Required("performance_max_temp", default=current_data.get("performance_max_temp", 70)): vol.All(
                    int, vol.Range(min=40, max=80)
                ),
                vol.Required("electric_min_temp", default=current_data.get("electric_min_temp", 60)): vol.All(
                    int, vol.Range(min=40, max=80)
                ),
                vol.Required("electric_max_temp", default=current_data.get("electric_max_temp", 70)): vol.All(
                    int, vol.Range(min=40, max=80)
                ),
            }),
            description_placeholders={
                "title": "Update Temperature Limits",
                "description": "Configure min/max temperatures for each operation mode"
            },
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update sensor settings with shared scaling."""
        if user_input is not None:
            self.data.update(user_input)
            return await self._update_and_reload()

        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema({
                vol.Optional("tank_top_temp_register", default=current_data.get("tank_top_temp_register", 101)): int,
                vol.Optional("tank_bottom_temp_register", default=current_data.get("tank_bottom_temp_register", 102)): int,
                vol.Optional("condensor_temp_register", default=current_data.get("condensor_temp_register", 103)): int,
                vol.Optional("outdoor_temp_register", default=current_data.get("outdoor_temp_register", 104)): int,
                vol.Optional("exhaust_temp_register", default=current_data.get("exhaust_temp_register", 105)): int,
                vol.Optional("suction_temp_register", default=current_data.get("suction_temp_register", 106)): int,
                vol.Optional("enable_additional_sensors", default=current_data.get("enable_additional_sensors", True)): bool,
                vol.Optional("sensors_temp_offset", default=current_data.get("sensors_temp_offset", -15.0)): vol.Coerce(float),
                vol.Optional("sensors_temp_scale", default=current_data.get("sensors_temp_scale", 0.5)): vol.Coerce(float),
            }),
            description_placeholders={
                "title": "Update Additional Sensors",
                "description": "Configure optional temperature sensors with shared offset and scale values"
            },
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update entity settings."""
        if user_input is not None:
            self.data.update(user_input)
            return await self._update_and_reload()

        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=current_data.get(CONF_NAME, "Hot Water System")): str,
                vol.Required("target_temperature", default=current_data.get("target_temperature", 65)): vol.All(
                    int, vol.Range(min=40, max=75)
                ),
            }),
            description_placeholders={
                "title": "Update Entity Settings",
                "description": "Modify entity name and default temperature"
            },
        )

    async def _update_and_reload(self) -> FlowResult:
        """Update config entry and reload."""
        # Merge the new data with existing data
        new_data = {**self.config_entry.data, **self.data}
        
        # Update the config entry
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data
        )
        
        # The update_listener in __init__.py will handle the reload automatically
        return self.async_create_entry(title="", data={})