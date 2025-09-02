# 🔥 Midea Heat Pump Water Heater ↔️ Home Assistant Integration

*Transform your Chromagen Midea 170L heat pump into a smart, Home Assistant-controlled water heater entity!*

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.1.1-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Midea-Heat-Pump-HA.svg)](https://github.com/0xAHA/Midea-Heat-Pump-HA/issues)

---

## 🎯 What You'll Achieve

This integration creates a fully functional **water heater entity** in Home Assistant that can:

- ✅ **Control operation modes**: Off, Eco, Performance, Electric
- ✅ **Set target temperature** via direct Modbus
- ✅ **Monitor real-time temperature** with configurable scaling
- ✅ **Integrate seamlessly** with automations, dashboards, and Lovelace cards
- ✅ **Follow HA standards** using proper water_heater domain

## 🏆 Features

- **Native water_heater entity** (not climate hack!)
- **Built-in Modbus client** (no external modbus dependency!)
- **Self-contained integration** - single configuration file
- **Proper operation modes** using HA standards
- **Real-time temperature monitoring** with configurable scaling
- **Direct register control** for all functions
- **Automatic polling** with configurable scan intervals

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

## 🏠 Home Assistant Configuration

### Single Configuration Setup

Add to your `configuration.yaml`:

```yaml
midea_heatpump_hws:
  water_heatpump:
    friendly_name: "Hot Water System"
  
    # Modbus connection
    modbus_host: 192.168.1.80  # Your RS485-WiFi Adapter IP address
    modbus_port: 502           # Your RS485-WiFi Adapter Modbus Port
    modbus_unit: 1
    scan_interval: 30
  
    # Register addresses
    temp_register: 102
    target_temp_register: 2
    mode_register: 1
    power_register: 0
  
    # Temperature scaling
    temp_offset: -15
    temp_scale: 0.5
  
    # Temperature settings
    target_temperature: 65
    min_temp: 40
    max_temp: 75
```

**Result**: Creates `water_heater.water_heatpump` entity with your chosen friendly name

**No external modbus.yaml setup required!** Everything is self-contained.

---

## 🎛️ Operation Modes


| Mode            | Description              | Midea Equivalent | Modbus Value |
| ----------------- | -------------------------- | ------------------ | -------------- |
| **Off**         | Water heater disabled    | Off              | -            |
| **Eco**         | Energy efficient heating | Economy mode     | 1            |
| **Performance** | High performance heating | Hybrid mode      | 2            |
| **Electric**    | Electric heating         | E-heater mode    | 4            |

## 🔬🤝 Operation Mode Compatibility

The operation modes are based on my own Midea unit. If you have other operation modes feel free to create a github issue to have them added to this integration. You can test yourself using a free modbus tester, and setting the value of register 1 to a different value (see above for the known output values for current modes)

---

## 🎨 Dashboard Integration

### Water Heater using Tile Card

```yaml
type: tile
entity: water_heater.water_heatpump
features_position: bottom
vertical: false
name: Water Heater
icon: mdi:water-boiler
state_content: current_temperature
features:
  - type: target-temperature
  - type: water-heater-operation-modes
    operation_modes:
      - "off"
      - eco
      - performance
      - electric
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
          entity_id: water_heater.water_heatpump
        data:
          operation_mode: "eco"

  - alias: "Heat pump performance mode morning"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.water_heatpump
        data:
          operation_mode: "performance"
```

### Temperature-based control

```yaml
automation:
  - alias: "Boost heating when temperature low"
    trigger:
      - platform: numeric_state
        entity_id: water_heater.water_heatpump
        attribute: current_temperature
        below: 45
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.water_heatpump
        data:
          operation_mode: "performance"
```

---

## 🔧 Troubleshooting

### Common Issues


| Issue                           | Solution                                       |
| --------------------------------- | ------------------------------------------------ |
| Entity shows as`unavailable`    | Check modbus host IP and network connectivity  |
| Target temperature not changing | Verify register addresses and modbus unit ID   |
| Modes not switching             | Check mode register values and power register  |
| Connection timeouts             | Verify RS485 Adapter is powered and accessible |

### Testing Other HWS Models

If you have a HWS system that doesn't suit these modbus registers, or has additional operating modes, use the python script referenced at the links below to check what's going on with your system and let us know!

* [Script README](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/README_Modbus.md)
* [Modbus Test Script](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/modbus_test.py)

### Debug Steps

1. **Check network connectivity** to your RS485 adapter
2. **Verify register addresses** match your heat pump model
3. **Check logs** for modbus connection errors
4. **Test registers manually** using Developer Tools
5. **Restart HA** after configuration changes

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

- [X] **Built-in Modbus integration** ✅ Completed in v0.1.0
- [ ] **Configuration UI** (no more YAML editing)
- [ ] **Enhanced diagnostics** (connection status, detailed error reporting)
- [ ] **Energy monitoring** (power consumption tracking)
- [ ] **Advanced scheduling** (built-in time/temperature profiles)
- [ ] **Multi-device support** (multiple heat pumps)

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

*Happy heating! 🔥*
