# 🔥 Midea Heat Pump ↔️ Home Assistant Integration

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

| Item | Description | Link |
|------|-------------|------|
| **EW-11A RS485 to WiFi** | The magic bridge (EW11A-0 + 4pin connector) | [AliExpress](https://www.aliexpress.com/item/32916128353.html) |
| **240VAC to DC PSU** | 12V recommended (5-18V supported) | *Your local electronics supplier* |
| **Jumper wires & terminals** | For neat connections | *Hardware store* |

---

## ⚡ Hardware Installation

> **⚠️ Safety First**: Have a licensed electrician handle the 240VAC connections!

### Step 1: Power Supply Installation
- Install appropriate PSU using available spade terminals inside the main HWS cover
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
- Locate the service connector outside the main panel (circled in green in images below)
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
- Update the host value in `modbus.yaml` to the IP address you have set for the EW-11A (or determine the DHCP address it has)
- This replaces basic climate entities with proper target temperature sensors

### Phase 3: Climate Template
- **Add** the climate template configuration to your `configuration.yaml`
- This creates the final climate entity with full control capabilities

---

## 📁 Required Files

| File | Purpose |
|------|---------|
| `modbus.yaml` | Defines Modbus sensors and target temperature control |
| `configuration.yaml` | Contains the climate template entity |

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
