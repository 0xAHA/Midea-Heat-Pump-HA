# Release Notes

## Version 0.2.4 - Sanitize Mode Support

### 🦠 New Features

#### Sanitize/Sterilize Mode
- **Dedicated sanitize switch** for hot water system hygiene and Legionella prevention
- **Automatic heating to 65°C** to kill bacteria in the hot water system
- **Override mode control** - Temporarily forces electric heating mode during sanitization
- **Auto-reset functionality** - Automatically disables when both tanks reach 65.5°C
- **Configurable register** - Sterilize register (default: 3) is optional during setup
- **Switch entity** - Appears as "Sanitize Mode" alongside the power switch

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
