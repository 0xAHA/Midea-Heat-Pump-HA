# 🔥 Midea Heat Pump Water Heater ↔️ Home Assistant Integration

*Transform your Midea/OEM heat pump hot water system into a smart, Home Assistant-controlled water heater entity!*

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.2.2-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Midea-Heat-Pump-HA.svg)](https://github.com/0xAHA/Midea-Heat-Pump-HA/issues)

---

## 🎯 What You'll Achieve

This integration creates a fully functional **water heater entity** in Home Assistant that can:

- ✅ **UI Configuration**: Configure entirely through the Home Assistant UI - no YAML required!
- ✅ **Mode-Specific Temperature Limits**: Enforces different min/max temperatures per operation mode
- ✅ **Control operation modes**: Off, Eco, Performance (Hybrid), Electric (E-Heater)
- ✅ **Set target temperature** via direct Modbus with automatic range enforcement
- ✅ **Monitor real-time temperature** with configurable scaling
- ✅ **Track multiple sensors**: Tank, outdoor, condensor temperatures and more
- ✅ **Integrate seamlessly** with automations, dashboards, and Lovelace cards
- ✅ **Follow HA standards** using proper water_heater domain

## 🏆 Features

- **Native water_heater entity** (not climate hack!)
- **UI-based configuration** with step-by-step setup wizard
- **Mode-specific temperature limits** (prevent Modbus errors from invalid temperatures)
- **Coordinated Modbus polling** - 90% reduction in network traffic!
- **Built-in Modbus client** (no external modbus dependency!)
- **Self-contained integration** - everything configured through UI
- **Proper operation modes** using HA standards
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

The integration's flexible configuration allows you to:
- Adjust all register addresses
- Configure temperature scaling and offsets
- Customize operation mode values
- Set mode-specific temperature limits
- Enable/disable sensors as needed

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

### UI Configuration (No YAML Required!)

Configure everything through the Home Assistant UI:

1. **Add Integration**:
   - Settings → Devices & Services → Add Integration
   - Search for "Midea Heatpump HWS"
   - Click to add

2. **Step 1: Connection Settings**
   - **Host**: IP address of your RS485-WiFi adapter (e.g., 192.168.1.80)
   - **Port**: Modbus TCP port (usually 502)
   - **Modbus Unit**: Device ID (usually 1)
   - **Scan Interval**: How often to poll (60-300 seconds recommended)

3. **Step 2: Control Registers**
   - Pre-configured for Midea units (no scaling needed):
     - **Power Register**: Control on/off (default: 0)
     - **Mode Register**: Operation mode (default: 1)
     - **Mode Values**: Eco=1, Performance=2, Electric=4

4. **Step 3: Temperature Registers**
   - Configure with individual scaling for each:
     - **Current Temperature Register**: (default: 102)
       - Offset: -15.0
       - Scale: 0.5
     - **Target Temperature Register**: (default: 2)
       - Offset: 0.0 (usually no scaling needed)
       - Scale: 1.0

5. **Step 4: Temperature Limits by Mode** *(New in v0.2.2)*
   - Set min/max temperatures for each operation mode:
     - **Eco Mode**: 60-65°C (default)
     - **Performance Mode**: 60-70°C (default)
     - **Electric Mode**: 60-70°C (default)
   - Prevents setting invalid temperatures that cause Modbus errors
   - UI automatically adjusts slider range based on current mode

6. **Step 5: Optional Sensors**
   - Enable/disable additional temperature sensors
   - Configure register addresses and shared scaling:
     - Tank top/bottom (101, 102)
     - Condensor (103), Outdoor (104)
     - Exhaust gas (105) - no scaling
     - Suction (106)
     - **Shared Offset**: -15.0
     - **Shared Scale**: 0.5

7. **Step 6: Entity Settings**
   - **Name**: Friendly name for your water heater
   - **Default Target**: Initial target temperature

### Reconfiguring

After initial setup, you can modify ALL settings without removing the integration:

1. **Access Configuration**:
   - Settings → Devices & Services → Midea Heatpump HWS → Configure
   
2. **Choose what to update**:
   - **Connection**: Modbus host, port, unit ID, scan interval
   - **Control Registers**: Power and mode registers (no scaling)
   - **Temperature Registers**: Temp registers with individual offset/scale
   - **Temperature Limits**: Min/max temperatures for each mode
   - **Sensors**: Additional sensor registers with shared offset/scale
   - **Settings**: Entity name and default target

3. **Apply changes**:
   - After updating any section, the integration automatically reloads
   - All entities update with new configuration immediately
   - No need to restart Home Assistant

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
| Tank Top Temp | 101 | T5U sensor | Configurable |
| Tank Bottom Temp | 102 | T5L sensor | Configurable |
| Condensor Temp | 103 | T3 sensor | Configurable |
| Outdoor Temp | 104 | T4 sensor | Configurable |
| Exhaust Gas Temp | 105 | Tp sensor | No scaling |
| Suction Temp | 106 | Th sensor | Configurable |

**Note**: Your heat pump model may use different registers. Use the configuration UI to adjust as needed.

---

## 🎨 Dashboard Integration

### Water Heater using Tile Card

```yaml
type: tile
entity: water_heater.hot_water_system
features:
  - type: target-temperature
  - type: water-heater-operation-modes
    operation_modes:
      - "off"
      - "eco"
      - "performance"
      - "electric"
```

### Temperature Sensors Card

```yaml
type: entities
entities:
  - entity: sensor.current_temperature
    name: Current Water Temp
  - entity: sensor.tank_top_temperature
    name: Tank Top
  - entity: sensor.tank_bottom_temperature
    name: Tank Bottom
  - entity: sensor.outdoor_temperature
    name: Outdoor
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
          entity_id: water_heater.hot_water_system
        data:
          operation_mode: "eco"

  - alias: "Heat pump performance mode morning"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.hot_water_system
        data:
          operation_mode: "performance"
```

### Temperature-based control

```yaml
automation:
  - alias: "Boost heating when temperature low"
    trigger:
      - platform: numeric_state
        entity_id: water_heater.hot_water_system
        attribute: current_temperature
        below: 45
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.hot_water_system
        data:
          operation_mode: "performance"
```

---

## 🚀 What's New in v0.2.2

### Mode-Specific Temperature Limits
- Each operation mode now has its own min/max temperature range
- Prevents Modbus errors from setting invalid temperatures
- UI slider automatically adjusts based on current mode
- Automatic target temperature adjustment when switching modes

### Enhanced Configuration
- 6-step configuration flow (expanded from 4)
- Separated control and temperature registers
- Individual scaling options for different temperature registers
- Complete reconfiguration without removing integration

### Improved Performance
- Immediate UI updates after commands (no waiting for next poll)
- Better error handling and validation
- Enhanced debug logging for troubleshooting

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

### Testing Other HWS Models

If you have a HWS system that uses different modbus registers or has additional operating modes:

1. Use the configuration UI to adjust register addresses
2. Test with the Python script to discover your registers:
   - [Script README](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/README_Modbus.md)
   - [Modbus Test Script](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/modbus_test.py)
3. Create a GitHub issue with your findings to help others!

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
- [ ] **Model profiles** (pre-configured settings for different models)
- [ ] **Enhanced diagnostics** (connection status, detailed error reporting)
- [ ] **Energy monitoring** (power consumption tracking)
- [ ] **Advanced scheduling** (built-in time/temperature profiles)
- [x] **Multi-device support** (multiple heat pumps)

---

## 🤝 Contributing

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
- 📢 **Share** with the community

*Happy heating!