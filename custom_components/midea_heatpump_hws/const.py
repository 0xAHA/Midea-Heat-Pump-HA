"""Constants for the Midea Heat Pump Water Heater integration."""
from homeassistant.const import Platform

DOMAIN = "midea_heatpump_hws"

PLATFORMS: list[Platform] = [Platform.WATER_HEATER, Platform.SENSOR, Platform.SWITCH, Platform.SELECT]

# Default register addresses
DEFAULT_POWER_REGISTER = 0
DEFAULT_MODE_REGISTER = 1
DEFAULT_TEMP_REGISTER = 102
DEFAULT_TARGET_TEMP_REGISTER = 2
DEFAULT_TANK_TOP_TEMP_REGISTER = 101
DEFAULT_TANK_BOTTOM_TEMP_REGISTER = 102
DEFAULT_CONDENSOR_TEMP_REGISTER = 103
DEFAULT_OUTDOOR_TEMP_REGISTER = 104
DEFAULT_EXHAUST_TEMP_REGISTER = 105
DEFAULT_SUCTION_TEMP_REGISTER = 106

# Default mode values
DEFAULT_ECO_MODE_VALUE = 1
DEFAULT_PERFORMANCE_MODE_VALUE = 2
DEFAULT_ELECTRIC_MODE_VALUE = 4

# Default temperature settings
DEFAULT_TEMP_OFFSET = -15.0
DEFAULT_TEMP_SCALE = 0.5
DEFAULT_TARGET_TEMP_OFFSET = 0.0
DEFAULT_TARGET_TEMP_SCALE = 1.0
DEFAULT_SENSORS_TEMP_OFFSET = -15.0
DEFAULT_SENSORS_TEMP_SCALE = 0.5
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_TARGET_TEMP = 65
DEFAULT_MIN_TEMP = 40
DEFAULT_MAX_TEMP = 75

# Mode Temperature limits
CONF_ECO_MIN_TEMP = "eco_min_temp"
CONF_ECO_MAX_TEMP = "eco_max_temp"
CONF_PERFORMANCE_MIN_TEMP = "performance_min_temp"
CONF_PERFORMANCE_MAX_TEMP = "performance_max_temp"
CONF_ELECTRIC_MIN_TEMP = "electric_min_temp"
CONF_ELECTRIC_MAX_TEMP = "electric_max_temp"

# Configuration keys
CONF_MODBUS_UNIT = "modbus_unit"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_POWER_REGISTER = "power_register"
CONF_MODE_REGISTER = "mode_register"
CONF_TEMP_REGISTER = "temp_register"
CONF_TARGET_TEMP_REGISTER = "target_temp_register"
CONF_ECO_MODE_VALUE = "eco_mode_value"
CONF_PERFORMANCE_MODE_VALUE = "performance_mode_value"
CONF_ELECTRIC_MODE_VALUE = "electric_mode_value"
CONF_TEMP_OFFSET = "temp_offset"
CONF_TEMP_SCALE = "temp_scale"
CONF_TARGET_TEMP_OFFSET = "target_temp_offset"
CONF_TARGET_TEMP_SCALE = "target_temp_scale"
CONF_SENSORS_TEMP_OFFSET = "sensors_temp_offset"
CONF_SENSORS_TEMP_SCALE = "sensors_temp_scale"
CONF_TARGET_TEMP = "target_temperature"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"

# Optional sensor registers
CONF_TANK_TOP_TEMP_REGISTER = "tank_top_temp_register"
CONF_TANK_BOTTOM_TEMP_REGISTER = "tank_bottom_temp_register"
CONF_CONDENSOR_TEMP_REGISTER = "condensor_temp_register"
CONF_OUTDOOR_TEMP_REGISTER = "outdoor_temp_register"
CONF_EXHAUST_TEMP_REGISTER = "exhaust_temp_register"
CONF_SUCTION_TEMP_REGISTER = "suction_temp_register"
CONF_ENABLE_ADDITIONAL_SENSORS = "enable_additional_sensors"