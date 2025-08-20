# 🔥 Midea Heat Pump ↔️ Home Assistant Integration

# 🔥 Midea Heat Pump Water Heater ↔️ Home Assistant Integration

*Transform your Chromagen Midea 170L heat pump into a smart, Home Assistant-controlled water heater entity!*

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/yourusername/midea-heatpump-ha.svg)](https://github.com/yourusername/midea-heatpump-ha/releases)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/midea-heatpump-ha.svg)](https://github.com/yourusername/midea-heatpump-ha/issues)

---

## 🎯 What You'll Achieve

This integration creates a fully functional **water heater entity** in Home Assistant that can:

* ✅  **Control operation modes** : Off, Eco, Hybrid (Performance)
* ✅ **Set target temperature** via Modbus
* ✅ **Monitor real-time temperature** from tank sensor
* ✅ **Integrate seamlessly** with automations, dashboards, and Lovelace cards
* ✅ **Follow HA standards** using proper water_heater domain

## 🏆 Features

* **Native water_heater entity** (not climate hack!)
* **Proper operation modes** using HA standards
* **Real-time temperature monitoring** from bottom-of-tank sensor
* **Direct Modbus control** for target temperature
* **Mode sync** with physical heat pump switches
* **Easy configuration** through YAML

---

## 📦 Installation

### Method 1: HACS (Recommended)

1. **Add custom repository** :
   * HACS → Integrations → ⋮ → Custom repositories
   * Repository: `https://github.com/yourusername/midea-heatpump-ha`
   * Category: Integration
2. **Install** :
   * Search for "Midea Heat Pump Water Heater"
   * Click Download
   * Restart Home Assistant

### Method 2: Manual Installation

1. **Download** the latest release from [GitHub releases](https://github.com/yourusername/midea-heatpump-ha/releases)
2. **Extract** to `/config/custom_components/generic_water_heater/`
3. **Restart** Home Assistant

---

## 🛠️ Hardware Requirements


| Item                         | Description                                 | Link                                                           |
| ------------------------------ | --------------------------------------------- | ---------------------------------------------------------------- |
| **EW-11A RS485 to WiFi**     | The magic bridge (EW11A-0 + 4pin connector) | [AliExpress](https://www.aliexpress.com/item/32916128353.html) |
| **240VAC to DC PSU**         | 12V recommended (5-18V supported)           | *Your local electronics supplier*                              |
| **Jumper wires & terminals** | For neat connections                        | *Hardware store*                                               |

---

## ⚡ Hardware Installation

> **⚠️ Safety First** : Have a licensed electrician handle the 240VAC connections!

### Step 1: Power Supply Installation

* Install appropriate PSU using available spade terminals inside the main HWS cover (circled in green in images below)
* Follow local electrical regulations

### Step 2: EW-11A Connections

**📍 Pin-out Reference**  *(left to right when looking down at screws)* :

```
Pin 1: Black  → RS485A from heater
Pin 2: Grey   → RS485B from heater  
Pin 3: Red    → VCC (5-18V DC)
Pin 4: Black  → GND from DC supply + Yellow GND from heater
```


<img width="772" height="214" alt="EW11-A connector pinout diagram" src="https://github.com/user-attachments/assets/92e0001d-2b15-4da6-9f66-24c7b342c4d9" />

### Step 3: RS485 Wiring

* Locate the service connector outside the main panel (circled in red in images below)
* Connect RS485 wires to the EW-11A 4-pin connector
* *Tip* : You can either remove pins for direct termination or use jumpers

<img width="480" height="466" alt="Heat pump internal connections" src="https://github.com/user-attachments/assets/cc9e1120-d59a-4429-9ee7-6fd3f841a29d" />
<img width="525" height="343" alt="EW11-A wiring diagram" src="https://github.com/user-attachments/assets/e0152cac-3086-4ed3-9c2a-4943a15ee336" />
---

## 📡 EW11-A Configuration

### Initial Setup

1. **Connect** to WiFi network `EWxxxxx` (based on MAC address)
2. **Browse** to `10.10.100.254`
3. **Login** with username: `admin`, password: `admin`

### Serial Port Settings

```
Baud Rate: 9600
Flow Control: Disable
Protocol: RS485
```

### Communications Settings

```
Socket Settings → Local Port: 502
```

### WiFi Configuration

1. **System Settings** → Change WiFi mode to `STA`
2. **Scan** for your network and enter credentials, OR manually enter:
   * STA SSID: `your_network_name`
   * STA KEY: `your_wifi_password`

### Optional: Static IP Setup

```
WAN Settings:
├── DHCP: Disabled
├── WAN IP: <IP address of your choice>
├── Subnet Mask: <as per your network>
├── Gateway: <your router's IP>
└── DNS: 8.8.8.8 or your preference
```

3. **Submit** and **restart** the EW11-A

---

## 🏠 Home Assistant Configuration

### Step 1: Modbus Setup

Create or update your `modbus.yaml` file:

```yaml
- name: waveshare1
  type: tcp
  host: 192.168.1.80  # Your EW11-A IP address
  port: 502
  delay: 2
  timeout: 5
  
  sensors:
    # Current temperature sensor
    - name: water_heatpump_temperature_bottom_of_tank_T5L
      unit_of_measurement: °C
      state_class: measurement
      unique_id: water_heatpump_temperature_bottom_of_tank_T5L
      scan_interval: 30
      address: 102
      slave: 1
      offset: -15
      scale: 0.5
  
    # Target temperature sensor (reads from register 2)
    - name: water_heatpump_target_temperature
      unit_of_measurement: °C
      state_class: measurement
      unique_id: water_heatpump_target_temperature
      scan_interval: 30
      address: 2
      slave: 1
      input_type: holding

  switches:
    # Main on/off switch
    - name: water_heatpump_on_off_toggle
      unique_id: water_heatpump_on_off_toggle
      address: 123  # Update with your actual register
      slave: 1
  
    # Mode switch (off=eco, on=hybrid)
    - name: water_heatpump_offeconomy_onhybrid_toggle
      unique_id: water_heatpump_offeconomy_onhybrid_toggle
      address: 124  # Update with your actual register
      slave: 1
```

### Step 2: Water Heater Configuration

Add to your `configuration.yaml`:

```yaml
generic_water_heater:
  water_heatpump:
    heater_switch: switch.water_heatpump_on_off_toggle
    mode_switch: switch.water_heatpump_offeconomy_onhybrid_toggle
    temperature_sensor: sensor.water_heatpump_temperature_bottom_of_tank_T5L
    target_temperature: 65
    min_temp: 40
    max_temp: 75
    modbus_hub: waveshare1
    modbus_unit: 1
    target_temp_register: 2
```

### Step 3: Restart Home Assistant

Your water heater entity will be created as `water_heater.water_heatpump`

---

## 🎛️ Operation Modes


| Mode            | Description              | Midea Equivalent |
| ----------------- | -------------------------- | ------------------ |
| **Off**         | Water heater disabled    | Off              |
| **Eco**         | Energy efficient heating | Economy mode     |
| **Performance** | High performance heating | Hybrid mode      |

---

## 🎨 Dashboard Integration

### Simple Thermostat Card

```yaml
type: thermostat
entity: water_heater.water_heatpump
```

### Water Heater Card

```yaml
type: water-heater-card
entity: water_heater.water_heatpump
```

### Custom Button Card

```yaml
type: custom:button-card
entity: water_heater.water_heatpump
show_state: true
show_icon: true
tap_action:
  action: more-info
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
* [ ] **Additional modes** (Electric/E-heater support)
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

This project is licensed under the MIT License - see the [LICENSE](https://claude.ai/chat/LICENSE) file for details.

---

## ⭐ Show Your Support

If this integration helped you, please:

* ⭐ **Star** this repository
* 🐛 **Report** any issues
* 💡 **Suggest** improvements
* 📢 **Share** with the community

*Happy heating! 🔥*

*Transform your Chromagen Midea 170L heat pump into a smart, Home Assistant-controlled powerhouse!*

---

## 🎯 What You'll Achieve

This guide walks you through creating a fully functional climate entity in Home Assistant that can:

- ✅ Control target temperature
- ✅ Turn the heat pump on/off
- ✅ Monitor real-time status
- ✅ Integrate with automations and dashboards

## 🧩 The Solution Overview

We're upgrading from basic Modbus sensors to a proper climate entity by:

1. **Installing** `hass-template-climate` from HACS
2. **Configuring** Modbus sensors in `modbus.yaml`
3. **Creating** a climate template in `configuration.yaml`

---

## 🛠️ Hardware Shopping List


| Item                         | Description                                 | Link                                                           |
| ------------------------------ | --------------------------------------------- | ---------------------------------------------------------------- |
| **EW-11A RS485 to WiFi**     | The magic bridge (EW11A-0 + 4pin connector) | [AliExpress](https://www.aliexpress.com/item/32916128353.html) |
| **240VAC to DC PSU**         | 12V recommended (5-18V supported)           | *Your local electronics supplier*                              |
| **Jumper wires & terminals** | For neat connections                        | *Hardware store*                                               |

---

## ⚡ Hardware Installation

> **⚠️ Safety First**: Have a licensed electrician handle the 240VAC connections!

### Step 1: Power Supply Installation

- Install appropriate PSU using available spade terminals inside the main HWS cover (circled in green in images below)
- Follow local electrical regulations

### Step 2: EW-11A Connections

**📍 Pin-out Reference** *(left to right when looking down at screws)*:

```
Pin 1: Black  → RS485A from heater
Pin 2: Grey   → RS485B from heater  
Pin 3: Red    → VCC (5-18V DC)
Pin 4: Black  → GND from DC supply + Yellow GND from heater
```

<img width="772" height="214" alt="EW11-A connector pinout diagram" src="https://github.com/user-attachments/assets/92e0001d-2b15-4da6-9f66-24c7b342c4d9" />

### Step 3: RS485 Wiring

- Locate the service connector outside the main panel (circled in red in images below)
- Connect RS485 wires to the EW-11A 4-pin connector
- *Tip*: You can either remove pins for direct termination or use jumpers

<img width="480" height="466" alt="Heat pump internal connections" src="https://github.com/user-attachments/assets/cc9e1120-d59a-4429-9ee7-6fd3f841a29d" />

<img width="525" height="343" alt="EW11-A wiring diagram" src="https://github.com/user-attachments/assets/e0152cac-3086-4ed3-9c2a-4943a15ee336" />

---

## 📡 EW11-A Configuration

### Initial Setup

1. **Connect** to WiFi network `EWxxxxx` (based on MAC address)
2. **Browse** to `10.10.100.254`
3. **Login** with username: `admin`, password: `admin`

### Serial Port Settings

Only the following should need changing:

```
Baud Rate: 9600
Flow Control: Disable
Protocol: RS485
```

### Communications Settings

Only the following should need changing:

```
Socket Settings → Local Port: 502
```

### WiFi Configuration

1. **System Settings** → Change WiFi mode to `STA`
2. **Scan** for your network and enter credentials, OR manually enter:
   - STA SSID: `your_network_name`
   - STA KEY: `your_wifi_password`

### Optional: Static IP Setup

```
WAN Settings:
├── DHCP: Disabled
├── WAN IP: <IP address of your choice>
├── Subnet Mask: <as per your network>
├── Gateway: <your router's IP>
└── DNS: 8.8.8.8 or your preference
```

3. **Submit** and **restart** the EW11-A

---

## 🏠 Home Assistant Configuration

### Phase 1: Install Template Climate

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. **Add**: `[https://github.com/jcwillox/hass-template-climate](https://github.com/jcwillox/hass-template-climate.git)`
3. Find the repo in HACS and **Download**, then **restart** Home Assistant

### Phase 2: Modbus Configuration

- **Place** the provided `modbus.yaml` in your HA config folder
- Update the **host** value in `modbus.yaml` to the IP address you have set for the EW-11A (or determine the DHCP address it has)
- This replaces basic climate entities with proper target temperature sensors

### Phase 3: Climate Template

- **Add** the climate template configuration to your `configuration.yaml`
- This creates the final climate entity with full control capabilities

---

## 📁 Required Files


| File                 | Purpose                                               |
| ---------------------- | ------------------------------------------------------- |
| `modbus.yaml`        | Defines Modbus sensors and target temperature control |
| `configuration.yaml` | Contains the climate template entity                  |

---

## 🙏 Credits & References

**Special thanks to:**

- **ill_hey** - Original HA Community post and instructions
- **BrittonA** - Initial Modbus YAML configuration

**Source threads:**

- [HA Community Discussion](https://community.home-assistant.io/t/chromagen-midea-170l-heat-pump-hot-water-system-modbus-integration-success/773718/12)
- [BrittonA's Gist](https://gist.github.com/BrittonA/339d25efb934bdb4f451ba7e2f920ba3)

---

## 🚀 Next Steps

Once configured, your heat pump will appear as a proper climate entity in Home Assistant, ready for:

- Dashboard cards
- Automations based on time/temperature
- Voice control integration
- Energy monitoring and optimization

*Happy heating! 🔥*
