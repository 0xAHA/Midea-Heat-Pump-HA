# 🔥 Midea Heat Pump Water Heater ↔️ Home Assistant Integration

*Transform your Chromagen Midea 170L heat pump into a smart, Home Assistant-controlled water heater entity!*

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.2.2-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Midea-Heat-Pump-HA.svg)](https://github.com/0xAHA/Midea-Heat-Pump-HA/issues)

---

## 🎯 What You'll Achieve

This integration creates a fully functional **water heater entity** in Home Assistant that can:

* ✅  **UI Configuration** : Configure entirely through the Home Assistant UI - no YAML required!
* ✅  **Control operation modes** : Off, Eco, Performance (Hybrid), Electric (E-Heater)
* ✅ **Set target temperature** via direct Modbus
* ✅ **Monitor real-time temperature** with configurable scaling
* ✅  **Track multiple sensors** : Tank, outdoor, condensor temperatures and more
* ✅ **Integrate seamlessly** with automations, dashboards, and Lovelace cards
* ✅ **Follow HA standards** using proper water_heater domain

## 🏆 Features

* **Native water_heater entity** (not climate hack!)
* **UI-based configuration** with step-by-step setup wizard
* **Coordinated Modbus polling** - 90% reduction in network traffic!
* **Built-in Modbus client** (no external modbus dependency!)
* **Self-contained integration** - everything configured through UI
* **Proper operation modes** using HA standards
* **Real-time temperature monitoring** with configurable scaling
* **Direct register control** for all functions
* **Automatic polling** with configurable scan intervals

---

## 📦 Installation

### Method 1: HACS (Recommended)

1. **Add custom repository** :
   * HACS → Integrations → ⋮ → Custom repositories
   * Repository: `https://github.com/0xAHA/Midea-Heat-Pump-HA.git`
   * Category: Integration
2. **Install** :
   * Search for "Midea Heatpump HWS"
   * Click Download
   * Restart Home Assistant

### Method 2: Manual Installation

1. **Download** the latest release from [here](https://github.com/0xAHA/Midea-Heat-Pump-HA)
2. **Extract** to `/config/custom_components/midea_heatpump_hws/`
3. **Restart** Home Assistant

---

## 🏠 Configuration

### UI Configuration (New in v0.2.0!)

No more YAML editing!

* If you were using a previous version, please remove the configuration from your configuration.yaml and modbus.yaml

Configure everything through the Home Assistant UI:

1. **Add Integration** :
   * Settings → Devices & Services → Add Integration
   * Search for "Midea Heatpump HWS"
   * Click to add
2. **Step 1: Connection Settings**
   * **Host** : IP address of your RS485-WiFi adapter (e.g., 192.168.1.80)
   * **Port** : Modbus TCP port (usually 502)
   * **Modbus Unit** : Device ID (usually 1)
   * **Scan Interval** : How often to poll (60-300 seconds recommended)
3. **Step 2: Register Configuration**
   * Pre-configured for Midea 170L units
   * Modify if your device uses different registers:
     * **Power Register** : Control on/off (default: 0)
     * **Mode Register** : Operation mode (default: 1)
     * **Temperature Register** : Current water temp (default: 102)
     * **Target Temp Register** : Set point (default: 2)
     * **Mode Values** : Eco=1, Performance=2, Electric=4
     * **Temperature Scaling** : Offset=-15, Scale=0.5
4. **Step 3: Optional Sensors**
   * Enable/disable additional temperature sensors
   * Configure register addresses for:
     * Tank top/bottom temperatures
     * Condensor temperature
     * Outdoor temperature
     * Exhaust gas temperature
     * Suction temperature
5. **Step 4: Entity Settings**
   * **Name** : Friendly name for your water heater
   * **Temperature Limits** : Min/max settable temperatures
   * **Default Target** : Initial target temperature

### Reconfiguring

After initial setup, you can modify ALL settings without removing the integration:

1. **Access Configuration** :
   * Settings → Devices & Services → Midea Heatpump HWS → Configure
2. **Choose what to update** :
   * **Connection** : Modbus host, port, unit ID, scan interval
   * **Registers** : All register addresses, mode values, temperature scaling
   * **Sensors** : Additional sensor registers and enable/disable
   * **Settings** : Entity name, temperature limits, default target
3. **Apply changes** :
   * After updating any section, the integration automatically reloads
   * All entities update with new configuration immediately
   * No need to restart Home Assistant

This allows complete flexibility to adjust for different heat pump models or troubleshoot issues without losing your automations and dashboard configurations!

---

## 🎛️ Operation Modes


| Mode            | Description              | Midea Equivalent | Modbus Value |
| ----------------- | -------------------------- | ------------------ | -------------- |
| **Off**         | Water heater disabled    | Off              | -            |
| **Eco**         | Energy efficient heating | Economy mode     | 1            |
| **Performance** | High performance heating | Hybrid mode      | 2            |
| **Electric**    | Electric heating         | E-heater mode    | 4            |

## 🔬 Register Reference

### Default Registers (Midea 170L)


| Function           | Register | Description    | Scaling           |
| -------------------- | ---------- | ---------------- | ------------------- |
| Power State        | 0        | On/Off control | None              |
| Operation Mode     | 1        | Current mode   | None              |
| Target Temperature | 2        | Set point      | None              |
| Tank Top Temp      | 101      | T5U sensor     | (raw × 0.5) - 15 |
| Tank Bottom Temp   | 102      | T5L sensor     | (raw × 0.5) - 15 |
| Condensor Temp     | 103      | T3 sensor      | (raw × 0.5) - 15 |
| Outdoor Temp       | 104      | T4 sensor      | (raw × 0.5) - 15 |
| Exhaust Gas Temp   | 105      | Tp sensor      | No scaling        |
| Suction Temp       | 106      | Th sensor      | (raw × 0.5) - 15 |

**Note** : Your heat pump model may use different registers. Use the configuration UI to adjust as needed.

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
      - "Off"
      - "Eco"
      - "Performance"
      - "Electric"
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
          operation_mode: "Eco"

  - alias: "Heat pump performance mode morning"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: water_heater.set_operation_mode
        target:
          entity_id: water_heater.hot_water_system
        data:
          operation_mode: "Performance"
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
          operation_mode: "Performance"
```

---

## 🚀 Performance Improvements (v0.2.0)

### Coordinator Pattern Implementation

The integration now uses a shared coordinator pattern for all Modbus communication:

* **Before** : Each entity polled independently → 10+ connections/minute
* **After** : Single coordinated poll → 1 connection/minute
* **Result** : **90% reduction in Modbus traffic!**

Benefits:

* Reduced load on RS485 adapters
* Synchronized entity updates
* Better error handling
* More reliable operation

---

## 🔧 Troubleshooting

### Common Issues


| Issue                           | Solution                                      |
| --------------------------------- | ----------------------------------------------- |
| Entity shows as`unavailable`    | Check modbus host IP and network connectivity |
| Target temperature not changing | Verify register addresses match your model    |
| Modes not switching             | Check mode register values and power register |
| Connection timeouts             | Increase scan interval in configuration       |
| Wrong temperature values        | Adjust temperature offset and scale in config |

### Testing Other HWS Models

If you have a HWS system that uses different modbus registers or has additional operating modes:

1. Use the configuration UI to adjust register addresses
2. Test with the Python script to discover your registers:
   * [Script README](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/README_Modbus.md)
   * [Modbus Test Script](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/modbus_test.py)
3. Create a GitHub issue with your findings to help others!

### Debug Logging

Available from the integrations UI, or add to `configuration.yaml`:

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

* **dgomes** - [Original Generic Water Heater](https://github.com/dgomes/ha_generic_water_heater)
* **ill_hey** - Original HA Community post and hardware instructions
* **BrittonA** - Initial Modbus YAML configuration

**Source threads:**

* [HA Community Discussion](https://community.home-assistant.io/t/chromagen-midea-170l-heat-pump-hot-water-system-modbus-integration-success/773718/12)
* [BrittonA&#39;s Gist](https://gist.github.com/BrittonA/339d25efb934bdb4f451ba7e2f920ba3)

---

## 📈 Roadmap

* [X] **Built-in Modbus integration** ✅ Completed in v0.1.0
* [X] **Configuration UI** ✅ Completed in v0.2.0
* [X] **Coordinated polling** ✅ Completed in v0.2.0
* [ ] **Enhanced diagnostics** (connection status, detailed error reporting) 🟠 Debug logs added in v0.2.1
* [ ] **Energy monitoring** (power consumption tracking)
* [ ] **Advanced scheduling** (built-in time/temperature profiles)
* [X] **Multi-device support** (multiple heat pumps) ✅ Completed in v0.2.0

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

* ⭐ **Star** this repository
* 🐛 **Report** any issues
* 💡 **Suggest** improvements
* 📢 **Share** with the community

*Happy heating! 🔥*
