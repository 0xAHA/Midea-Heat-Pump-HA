# 🔥 Midea Heat Pump Water Heater ↔️ Home Assistant Integration

*Transform your Midea/OEM heat pump hot water system into a smart, Home Assistant-controlled water heater entity!*

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.2.4-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Midea-Heat-Pump-HA.svg)](https://github.com/0xAHA/Midea-Heat-Pump-HA/issues)

---

## 🎯 What You'll Achieve

This integration creates a fully functional **water heater entity** in Home Assistant that can:

- ✅ **Profile System**: Load from pre-configured profiles or save your own for easy setup and sharing
- ✅ **UI Configuration**: Configure entirely through the Home Assistant UI - no YAML required!
- ✅ **Sanitize/Sterilize Mode**: Dedicated switch for hot water sanitization (heats to 65°C to kill bacteria)
- ✅ **Mode-Specific Temperature Limits**: Enforces different min/max temperatures per operation mode
- ✅ **Control operation modes**: Off, Eco, Performance (Hybrid), Electric (E-Heater)
- ✅ **Set target temperature** via direct Modbus with automatic range enforcement
- ✅ **Monitor real-time temperature** with configurable scaling
- ✅ **Track multiple sensors**: Tank, outdoor, condensor temperatures and more
- ✅ **Multiple device support**: Configure multiple water heaters with unique entities
- ✅ **Integrate seamlessly** with automations, dashboards, and Lovelace cards
- ✅ **Follow HA standards** using proper water_heater domain

## 🏆 Features

- **Profile-based setup** - Quick configuration using pre-defined or custom profiles
- **Native water_heater entity** (not climate hack!)
- **UI-based configuration** with step-by-step setup wizard
- **Mode-specific temperature limits** (prevent Modbus errors from invalid temperatures)
- **Coordinated Modbus polling** - 90% reduction in network traffic!
- **Built-in Modbus client** (no external modbus dependency!)
- **Self-contained integration** - everything configured through UI
- **Profile export/import** - Share configurations with the community
- **Real-time temperature monitoring** with configurable scaling
- **Direct register control** for all functions
- **Automatic polling** with configurable scan intervals

---

## 🎛️ Compatibility

### Primary Target
This integration is primarily developed for the **Chromagen Midea 170L Heat Pump (Model: HP170 / RSJ-15/190RDN3-C)**, but the highly configurable nature makes it compatible with:

### Also Compatible With
- **Other OEM-branded Midea units** (many manufacturers rebrand Midea heat pumps)
- **Similar Modbus-controllable hot water systems**
- **Different capacity Midea models** (200L, 300L, etc.)
- **Other heat pump water heaters** with Modbus RTU over TCP support

The integration's flexible configuration and profile system allows you to:
- Load pre-configured profiles for known models
- Adjust all register addresses
- Configure temperature scaling and offsets
- Customize operation mode values
- Set mode-specific temperature limits
- Enable/disable sensors as needed
- Save and share your configuration as a profile

This means if your hot water system uses Modbus communication, you can likely adapt this integration to work with it!

---

## 📦 Installation

### Method 1: HACS (Recommended)

1. **Add custom repository**:
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/0xAHA/Midea-Heat-Pump-HA.git`
   - Category: Integration

2. **Install**:
   - Search for "Midea Heatpump HWS"
   - Click Download
   - Restart Home Assistant

### Method 2: Manual Installation

1. **Download** the latest release from [here](https://github.com/0xAHA/Midea-Heat-Pump-HA)
2. **Extract** to `/config/custom_components/midea_heatpump_hws/`
3. **Restart** Home Assistant

---

## 🏠 Configuration

### Profile-Based Setup (New in v0.2.3!)

The integration now includes a profile system for quick and easy configuration:

#### Using Pre-configured Profiles

1. **Add Integration**:
   - Settings → Devices & Services → Add Integration
   - Search for "Midea Heatpump HWS"

2. **Choose Setup Method**:
   - Select **"Load from Profile"** for quick setup
   - Select **"Manual Configuration"** for custom setup

3. **If using Profile**:
   - Choose from available profiles (e.g., "Midea 170L Heat Pump")
   - Enter your device's IP address
   - Enter a friendly name
   - Done! All registers and settings are pre-configured

#### Manual Configuration

If choosing manual setup or your model isn't in the profiles:

1. **Step 1: Connection Settings**
   - **Host**: IP address of your RS485-WiFi adapter
   - **Port**: Modbus TCP port (usually 502)
   - **Modbus Unit**: Device ID (usually 1)
   - **Scan Interval**: How often to poll (60-300 seconds)

2. **Step 2: Control Registers**
   - Power Register (default: 0)
   - Mode Register (default: 1)
   - Mode Values (Eco=1, Performance=2, Electric=4)

3. **Step 3: Temperature Registers**
   - Current Temperature Register (default: 102)
   - Target Temperature Register (default: 2)
   - Individual scaling options for each

4. **Step 4: Temperature Limits by Mode**
   - Eco Mode: 60-65°C (default)
   - Performance Mode: 60-70°C (default)
   - Electric Mode: 60-70°C (default)

5. **Step 5: Optional Sensors**
   - Configure additional temperature sensors
   - Shared scaling for sensor group

6. **Step 6: Entity Settings**
   - Friendly name
   - Default target temperature

7. **Step 7: Save as Profile** (Optional)
   - Save your configuration for future use
   - Share with the community

### Reconfiguring

Access all settings without removing the integration:
- Settings → Devices & Services → Midea Heatpump HWS → Configure
- Options include:
  - Connection Settings
  - Control Registers
  - Temperature Registers
  - Temperature Limits
  - Sensors
  - Entity Settings
  - **Save as Profile** - Save current configuration

---

## 📤 Profile Management

### Exporting Profiles

Share your working configuration with others:

1. **Via Service Call**:
   ```yaml
   service: midea_heatpump_hws.export_profile
   data:
     name: "My 170L Config"
     model: "HP170"
   ```

2. **Via Developer Tools**:
   - Developer Tools → Services
   - Select `midea_heatpump_hws.export_profile`
   - Enter optional name and model
   - Call Service
   - Right-click the download link in the notification to save

3. **Via Configuration Menu**:
   - Settings → Devices & Services → Your Device → Configure
   - Select "Save as Profile"
   - Enter profile name and model
   - Profile saved for future use

### Profile Structure

Profiles are JSON files containing all configuration:
- Register addresses
- Scaling factors
- Temperature limits
- Mode values
- Default settings

Example profile location:
- Built-in: `/custom_components/midea_heatpump_hws/models/defaults/`
- Custom: `/custom_components/midea_heatpump_hws/models/custom/`

### Sharing Profiles

Exported profiles can be:
- Shared on GitHub issues for others with the same model
- Kept as configuration backups
- Used for quick setup of multiple units

---

## 🎛️ Operation Modes

| Mode | Description | Midea Equivalent | Modbus Value | Temp Range* |
|------|-------------|------------------|--------------|-------------|
| **off** | Water heater disabled | Off | - | - |
| **eco** | Energy efficient heating | Economy mode | 1 | 60-65°C |
| **performance** | High performance heating | Hybrid mode | 2 | 60-70°C |
| **electric** | Electric heating | E-heater mode | 4 | 60-70°C |

*Temperature ranges are configurable per mode during setup

## 🔬 Register Reference

### Default Registers (Midea 170L)

| Function | Register | Description | Scaling |
|----------|----------|-------------|---------|
| Power State | 0 | On/Off control | None |
| Operation Mode | 1 | Current mode | None |
| Target Temperature | 2 | Set point | Configurable |
| Sterilize Mode | 3 | Sanitize/sterilize mode | None |
| Tank Top Temp | 101 | T5U sensor | Configurable |
| Tank Bottom Temp | 102 | T5L sensor | Configurable |
| Condensor Temp | 103 | T3 sensor | Configurable |
| Outdoor Temp | 104 | T4 sensor | Configurable |
| Exhaust Gas Temp | 105 | Tp sensor | No scaling |
| Suction Temp | 106 | Th sensor | Configurable |

**Note**: Your heat pump model may use different registers. Use the configuration UI to adjust as needed, then save as a custom profile.

### 🦠 Sanitize/Sterilize Mode

The integration includes a dedicated switch for hot water sanitization mode (register 3):

- **Purpose**: Heats water to 65°C to kill bacteria (Legionella prevention)
- **Operation**: When enabled, overrides normal operation mode and forces electric heating
- **Target Temperature**: Automatically set to 65°C during sanitization
- **Auto-Reset**: System automatically turns off sanitize mode when both tanks reach 65.5°C
- **Switch Entity**: Appears as "Sanitize Mode" switch alongside the power switch
- **Recommended Use**: Run weekly or as needed for water system hygiene

**Note**: The sanitize switch is created automatically if the sterilize_register is configured (default: register 3).

---

## 🎨 Dashboard Integration

### Water Heater using Tile Card

```yaml
type: tile
entity: water_heater.hot_water_system_192_168_1_80
features:
  - type: target-temperature
  - type: water-heater-operation-modes
    operation_modes:
      - "off"
      - "eco"
      - "performance"
      - "electric"
```

### Water Heater with Sanitize Mode

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: water_heater.hot_water_system_192_168_1_80
    features:
      - type: target-temperature
      - type: water-heater-operation-modes
        operation_modes:
          - "off"
          - "eco"
          - "performance"
          - "electric"
  - type: tile
    entity: switch.sanitize_mode_192_168_1_80
    name: Sanitize Mode
    icon: mdi:water-boiler
```

### Multiple Water Heaters

```yaml
type: vertical-stack
cards:
  - type: tile
    entity: water_heater.hot_water_system_192_168_1_80
    name: Main House
  - type: tile
    entity: water_heater.hot_water_system_192_168_1_81
    name: Guest House
```

---

## 🤖 Automation Examples

### Time-based heating schedule

```yaml
automation:
  - alias: "Heat pump eco mode at night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.hot_water_system_192_168_1_80
        data:
          operation_mode: "eco"
```

### Temperature-based control

```yaml
automation:
  - alias: "Boost heating when temperature low"
    trigger:
      - platform: numeric_state
        entity_id: water_heater.hot_water_system_192_168_1_80
        attribute: current_temperature
        below: 45
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.hot_water_system_192_168_1_80
        data:
          operation_mode: "performance"
```

### Weekly sanitization schedule

```yaml
automation:
  - alias: "Weekly hot water sanitization"
    trigger:
      - platform: time
        at: "02:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.sanitize_mode_192_168_1_80
      - service: notify.mobile_app
        data:
          title: "Hot Water System"
          message: "Weekly sanitization cycle started"
```

---

## 🚀 What's New in v0.2.4

### Sanitize/Sterilize Mode Support
- **Dedicated sanitize switch** for hot water system hygiene
- **Automatic heating to 65°C** to kill bacteria (Legionella prevention)
- **Override system** that temporarily takes control of operation mode
- **Auto-reset feature** when target temperature reached
- **Configurable register** (default: register 3, optional in setup)
- **EcoSpring HP300 profile** added to default profiles

### Bug Fixes & Improvements
- Added Python cache files to .gitignore
- Improved register documentation in README
- Enhanced modbus_test.py with sterilize register support

### Previous Features (v0.2.3)
- Profile system with pre-configured models
- Multiple device support with unique entity naming
- Export/import profiles for community sharing
- Enhanced services for profile management

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Entity shows as `unavailable` | Check modbus host IP and network connectivity |
| Target temperature not changing | Verify register addresses match your model |
| Temperature rejected (Modbus error) | Check mode-specific temperature limits |
| Modes not switching | Check mode register values and power register |
| Connection timeouts | Increase scan interval in configuration |
| Wrong temperature values | Adjust temperature offset and scale in config |
| Multiple devices conflict | Each device needs unique IP address |

### Testing Other HWS Models

If you have a HWS system that uses different modbus registers:

1. Configure manually (don't use a profile)
2. Test and adjust register addresses as needed
3. Once working, save as a custom profile
4. Export and share your profile on GitHub!

### Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.midea_heatpump_hws: debug
    custom_components.midea_heatpump_hws.coordinator: debug
```

---

## 🙏 Credits & References

**Based on the excellent work of:**
- **dgomes** - [Original Generic Water Heater](https://github.com/dgomes/ha_generic_water_heater)
- **ill_hey** - Original HA Community post and hardware instructions
- **BrittonA** - Initial Modbus YAML configuration

**Source threads:**
- [HA Community Discussion](https://community.home-assistant.io/t/chromagen-midea-170l-heat-pump-hot-water-system-modbus-integration-success/773718/12)
- [BrittonA's Gist](https://gist.github.com/BrittonA/339d25efb934bdb4f451ba7e2f920ba3)

---

## 📈 Roadmap

- [x] **Built-in Modbus integration** ✅ Completed in v0.1.0
- [x] **Configuration UI** ✅ Completed in v0.2.0
- [x] **Coordinated polling** ✅ Completed in v0.2.1
- [x] **Mode-specific temperature limits** ✅ Completed in v0.2.2
- [x] **Profile system** ✅ Completed in v0.2.3
- [x] **Multiple device support** ✅ Completed in v0.2.3
- [ ] **Community profile library** (shared configurations)
- [ ] **Enhanced diagnostics** (connection status, detailed error reporting)
- [ ] **Energy monitoring** (power consumption tracking)
- [ ] **Advanced scheduling** (built-in time/temperature profiles)

---

## 🤝 Contributing

### Share Your Profile!

If you have a working configuration for a different model:
1. Export your profile using the service
2. Create a GitHub issue with your profile attached
3. Include your water heater model and any notes
4. Help others with the same model!

### Development

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/LICENSE) file for details.

---

## ⭐ Show Your Support

If this integration helped you, please:
- ⭐ **Star** this repository
- 🐛 **Report** any issues
- 💡 **Suggest** improvements
- 📤 **Share** your device profile
- 📢 **Share** with the community

*Happy heating! 🔥*