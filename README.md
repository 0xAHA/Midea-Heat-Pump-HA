# 🔥 Midea Heat Pump Water Heater ↔️ Home Assistant Integration

*Transform your Chromagen Midea 170L heat pump into a smart, Home Assistant-controlled water heater entity!*

![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/Version-0.0.2-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/0xAHA/Midea-Heat-Pump-HA.svg)](https://github.com/0xAHA/Midea-Heat-Pump-HA/issues)

---

## 🎯 What You'll Achieve

This integration creates a fully functional **water heater entity** in Home Assistant that can:

* ✅  **Control operation modes** : Off, Eco, Hybrid (Performance), E-Heater (Electric)
* ✅ **Set target temperature** via Modbus
* ✅ **Monitor real-time temperature** from tank sensor
* ✅ **Integrate seamlessly** with automations, dashboards, and Lovelace cards
* ✅ **Follow HA standards** using proper water_heater domain

## 🏆 Features

* **Native water_heater entity** (not climate hack!)
* **Proper operation modes** using HA standards
* **Real-time temperature monitoring** from bottom-of-tank sensor
* **Direct Modbus control** for target temperature
* **Mode sync** with physical heat pump setting
* **Easy configuration** through YAML

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

## 🛠️ Hardware Requirements

Follow the hardware installation instructions [here](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/README_Hardware.md)

Once completed and tested, you should be ready to integrate to Home Assistant.

---

## 🏠 Home Assistant Configuration

### Step 1: Modbus Setup

Create or update your `modbus.yaml` file using the example [here](https://github.com/0xAHA/Midea-Heat-Pump-HA/blob/main/files/modbus.yaml)

### Step 2: Water Heater Configuration

Add to your `configuration.yaml`:

```yaml
modbus: !include modbus.yaml

midea_heatpump_hws:
  water_heatpump:
    heater_switch: switch.water_heatpump_on_off_toggle
    mode_sensor: sensor.water_heatpump_mode   
    temperature_sensor: sensor.water_heatpump_temperature_bottom_of_tank_T5L
    target_temperature: 65
    min_temp: 60
    max_temp: 65
    modbus_hub: waveshare1
    modbus_unit: 1
    target_temp_register: 2
```

### Step 3: Restart Home Assistant

Your water heater entity will be created as `water_heater.water_heatpump`

---

## 🎛️ Operation Modes


| Mode            | Description              | Midea Equivalent | Modbus Value |
| ----------------- | -------------------------- | ------------------ | -------------- |
| **Off**         | Water heater disabled    | Off              |              |
| **Eco**         | Energy efficient heating | Economy mode     | 1            |
| **Performance** | High performance heating | Hybrid mode      | 2            |
| **Electric**    | Electric heating         | E-heater mode    | 4            |

## 🔬🤝 Operation Mode Compatibility

The operation modes are based on my own Midea unit. If you have other operation modes feel free to create a github issue to have them added to this integration. You can test yourself using a free modbus tester, and setting the value of register 1 to a different value (see above for the known output values for current modes)

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


| Issue                           | Solution                                    |
| --------------------------------- | --------------------------------------------- |
| Entity shows as`unavailable`    | Check modbus connection and sensor entities |
| Target temperature not changing | Verify modbus hub name and register address |
| Modes not switching             | Check switch entity names in configuration  |

### Debug Steps

1. **Check modbus sensors** are working in Developer Tools → States
2. **Verify switch operations** manually before configuring water heater
3. **Check logs** for any custom component errors
4. **Restart HA** after configuration changes

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

* [ ] **Full Modbus integration** (eliminate external modbus dependency)
* [ ] **Enhanced diagnostics** (error reporting, connection status)
* [ ] **Energy monitoring** (power consumption tracking)
* [ ] **Advanced scheduling** (built-in time/temperature profiles)

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
