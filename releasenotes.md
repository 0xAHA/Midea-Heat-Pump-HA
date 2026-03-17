# Release Notes

## Version 0.2.5 - Heater Assist & Sanitize Status Sensors

### ✨ New Features

#### Heater Assist Binary Sensor (EcoSpring HP300 and compatible models)

Some heat pump water heaters contain a resistance heating element that activates automatically alongside the heat pump compressor — this is called **heater assist**. It is distinct from:

- **Electric mode** (mode value 4) — which runs the resistance element *instead of* the heat pump
- **Performance/Hybrid mode** — which is a user-selected mode; heater assist may activate even in Eco mode if the unit decides it needs extra capacity

Register 108 exposes the firmware substate that indicates whether this element is currently active. The new **Heater Assist** binary sensor shows:

| State | Meaning |
|-------|---------|
| `Off` | Resistance element not active (register 108 = 0) |
| `On` | Resistance element currently supplementing the heat pump (register 108 ≠ 0) |

#### Sanitize Cycle Active Binary Sensor

The existing **Sanitize Mode switch** (register 3) is a write-only control — you turn it on to trigger a sanitize cycle, but previously had no way to confirm the cycle was running or when it completed.

Register 109 is a read-only status register that reports the active sanitize cycle phase. The new **Sanitize Cycle Active** binary sensor shows:

| State | Register 109 value | Meaning |
|-------|--------------------|---------|
| `Off` | 0 | No sanitize cycle running |
| `On` | 32 | Sanitize cycle actively running (immediate trigger) |
| `On` | 33 | Sanitize cycle actively running (delayed/scheduled) |

> **Note**: A value of 2 in register 109 accompanies heater assist activity and does **not** indicate a sanitize cycle.

#### How to use these sensors in automations

```yaml
# Notify when a sanitize cycle completes
automation:
  - alias: "Notify when sanitize cycle finishes"
    trigger:
      - platform: state
        entity_id: binary_sensor.sanitize_cycle_active_192_168_1_80
        from: "on"
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "Hot Water System"
          message: "Sanitize cycle complete — system returned to normal operation"

# Alert if heater assist runs for an extended period (may indicate heat pump issue)
automation:
  - alias: "Alert if resistance heating runs too long"
    trigger:
      - platform: state
        entity_id: binary_sensor.heater_assist_192_168_1_80
        to: "on"
        for: "02:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Hot Water System"
          message: "Resistance heater has been running for 2+ hours — check unit"
```

### 📝 Debug Logging

Both binary sensors log the raw register value alongside the derived On/Off state on every coordinator update:

```
binary_sensor: Heater Assist (192.168.1.80): register 108 raw=13 -> is_on=True
binary_sensor: Sanitize Cycle Active (192.168.1.80): register 109 raw=32 -> is_on=True
```

Enable with:

```yaml
logger:
  logs:
    custom_components.midea_heatpump_hws: debug
```

### 🔧 EcoSpring HP300 Profile Updated (v1.1)

- Minimum temperature corrected from **60°C to 55°C** across all modes, based on community testing (GitHub issue #25)
- Model name updated to cover both 280L and 300L variants
- Registers 108 and 109 added to the profile — sensors appear automatically when loading this profile

### ⚠️ Upgrade Notes

- **Existing EcoSpring HP300 users**: Re-run setup using the updated profile to get the corrected temperature limits and the two new sensors. Your existing entities will not change names.
- **Other models**: No changes. The binary sensors only appear when `heater_assist_register` and/or `sanitize_state_register` are present in your loaded profile.
- **No breaking changes**: Fully backward compatible with v0.2.4.

### 📦 Files Changed

- `custom_components/midea_heatpump_hws/binary_sensor.py` — New platform with `MideaBinarySensor` class
- `custom_components/midea_heatpump_hws/const.py` — Added `CONF_HEATER_ASSIST_REGISTER`, `CONF_SANITIZE_STATE_REGISTER`; added `Platform.BINARY_SENSOR`
- `custom_components/midea_heatpump_hws/coordinator.py` — Reads registers 108/109 as raw integers
- `custom_components/midea_heatpump_hws/sensor.py` — Removed obsolete `MideaStateSensor` class
- `custom_components/midea_heatpump_hws/profile_manager.py` — Propagates new registers through apply/save
- `custom_components/midea_heatpump_hws/models/defaults/ecospring_hp300.json` — v1.1 with corrected limits and new registers
- `custom_components/midea_heatpump_hws/manifest.json` — Version bumped to 0.2.5; `binary_sensor` added to dependencies
- `README.md` — Updated for v0.2.5

### 🙏 Acknowledgments

Thanks to **tazomatalax** for the detailed register reverse-engineering documented in GitHub issue #25!

---

## Version 0.2.4 - Sanitize Mode Support

### 🦠 New Features

#### Sanitize/Sterilize Mode (Optional Feature)
- **Optional sanitize switch** for models that support hot water sanitization
- **Simple on/off control** - Integration writes only to register 3 (0=off, 1=on)
- **Hardware-controlled behavior** - The heat pump automatically handles:
  - Mode override (switches to electric heating)
  - Temperature control (sets to 65°C)
  - Auto-reset when complete (both tanks reach 65.5°C)
- **Not enabled by default** - Sterilize register is optional in setup
- **Conditional switch** - Only appears if sterilize_register is configured
- **Profile support** - EcoSpring HP300 profile includes sanitize register pre-configured

#### New Profile
- **EcoSpring HP300** profile added to default profiles for easy configuration

### 📋 How Sanitize Mode Works

1. When enabled via the switch, register 3 is set to `1`
2. The heat pump:
   - Overrides the current operating mode
   - Forces electric heating (E-heater mode)
   - Sets target temperature to 65°C
3. When both tanks reach 65.5°C, the hardware automatically:
   - Resets register 3 to `0`
   - Returns to normal operation mode
4. The switch state updates on the next poll cycle

### 💡 Usage Recommendations

- **Weekly sanitization**: Run once per week to prevent bacteria buildup
- **Automation friendly**: Easily schedule via Home Assistant automations
- **Health & safety**: Helps prevent Legionella and other waterborne bacteria
- **Automatic completion**: No need to manually turn off - system handles it

### 🛠️ Configuration

The sterilize register can be configured during setup:
- Default: Register 3
- Location: Control Registers step (optional field)
- The sanitize switch only appears if a sterilize register is configured

### 🔧 Bug Fixes & Improvements

- **Enhanced .gitignore**: Added Python cache files (`__pycache__/`, `*.pyc`, etc.)
- **Updated documentation**: Improved register reference table in README
- **Enhanced testing tool**: Added sterilize register to modbus_test.py output
- **Better translations**: Added strings for sterilize register in config flow

### 📚 Updated Documentation

- Added sanitize mode section to README
- New automation example for weekly sanitization scheduling
- Updated dashboard integration examples with sanitize switch
- Enhanced register reference table

### 📦 Files Changed

- `custom_components/midea_heatpump_hws/const.py` - Added sterilize register constants
- `custom_components/midea_heatpump_hws/config_flow.py` - Added sterilize register to setup
- `custom_components/midea_heatpump_hws/coordinator.py` - Added read/write for sterilize mode
- `custom_components/midea_heatpump_hws/switch.py` - Added MideaSterilizeSwitch entity
- `custom_components/midea_heatpump_hws/strings.json` - Added translations for sterilize register
- `custom_components/midea_heatpump_hws/models/defaults/ecospring_hp300.json` - New profile
- `files/modbus_test.py` - Added sterilize register to test output
- `.gitignore` - Added Python cache patterns
- `README.md` - Comprehensive updates for v0.2.4
- `manifest.json` - Version bump to 0.2.4

### 🔄 Upgrade Notes

- **Existing installations**: The sanitize switch will appear automatically if register 3 is readable
- **New installations**: Sterilize register (3) is included by default in setup
- **Custom configurations**: Can be added via Configure → Control Registers
- **No breaking changes**: Fully backward compatible with v0.2.3

### 🙏 Acknowledgments

Thanks to the community member who requested and tested this feature with their EcoSpring HP300 system!

---

## Previous Releases

### Version 0.2.3 - Profile System
- Profile-based setup with pre-configured models
- Multiple device support with unique entity naming
- Export/import profiles for community sharing
- Enhanced services for profile management

### Version 0.2.2 - Temperature Limits
- Mode-specific temperature limits
- Enhanced 6-step configuration flow
- Immediate UI updates after commands
- Better error handling and validation

### Version 0.2.1 - Coordinated Polling
- 90% reduction in network traffic
- Single coordinator for all entities
- Improved reliability and performance

### Version 0.2.0 - UI Configuration
- Complete UI-based setup wizard
- No YAML configuration required
- Options flow for reconfiguration

### Version 0.1.0 - Initial Release
- Native water_heater entity
- Built-in Modbus support
- Basic temperature control
