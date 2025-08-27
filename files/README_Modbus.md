# Water Heat Pump Modbus Testing Script

A comprehensive Python script for reading, testing, and discovering Modbus registers on water heat pump systems. Designed to help integrate water heat pumps with Home Assistant and document unknown register mappings.

## 🎯 Purpose

This script helps you:

* **Monitor** your water heat pump's current status and sensor readings
* **Discover** new operating modes by safely testing write operations
* **Map** unknown registers to find additional sensors and data points
* **Validate** Home Assistant Modbus configurations
* **Contribute** to the community by documenting new register mappings

## ✨ Features

### 🔍 **Three Operating Modes**


| Mode        | Flag     | Purpose        | Description                                                         |
| ------------- | ---------- | ---------------- | --------------------------------------------------------------------- |
| **Default** | *(none)* | Monitor Status | Read all known water heater registers and display current values    |
| **Test**    | `-t`     | Discover Modes | Interactively test write operations to discover new operating modes |
| **Map**     | `-m`     | Scan Registers | Scan register ranges to discover available data points              |

### 🌡️ **Smart Temperature Detection**

* Automatically applies known scaling formulas from your Home Assistant config
* Tests multiple temperature interpretations for unknown registers
* Identifies potential temperature sensors with realistic value ranges

### 🔧 **Interactive Testing**

* Safe write testing with error handling and verification
* Tracks successful/failed attempts with detailed error codes
* Prevents accidental damage with validation and warnings

## 📋 Requirements

```bash
pip install pymodbus
```

## 🚀 Usage

### Basic Syntax

```bash
python modbus_test.py <ip_address> <port> [options]
```

### 📊 Default Mode - Monitor Status

Read all known water heat pump registers:

```bash
python modbus_test.py 192.168.1.80 502
```

**Example Output:**

```
🌡️  Water Heat Pump Status - 192.168.1.80:502
================================================================================
✅ Connected successfully

Register Name                               Raw Value    Processed Value    Description
-------------------------------------------------------------------------------------
0        Power State                        1 (0x0001)   ON                 On/Off Status
1        Operating Mode                     2 (0x0002)   Hybrid             Heat pump mode
2        Target Temperature                 65 (0x0041)  65 °C              Set point temperature
101      Tank Top Temperature (T5U)         80 (0x0050)  25.0 °C            Top of tank temperature
102      Tank Bottom Temperature (T5L)      154 (0x009A) 62.0 °C            Bottom of tank temperature
103      Condensor Temperature (T3)         77 (0x004D)  23.5 °C            Condensor temperature
104      Outdoor Temperature (T4)           75 (0x004B)  22.5 °C            Ambient outdoor temperature
105      Exhaust Gas Temperature (Tp)       27 (0x001B)  27 °C              Compressor exhaust temperature
106      Suction Temperature (Th)           81 (0x0051)  25.5 °C            Compressor suction temperature
-------------------------------------------------------------------------------------
Successfully read 9/9 registers
```

### 🧪 Test Mode - Discover Operating Modes

Safely test write operations to discover new modes:

```bash
python modbus_test.py 192.168.1.80 502 -t
```

**Interactive Commands:**

* `0-255`: Test writing a specific mode value
* `r`: Read current operating mode
* `q`: Quit test mode

**Example Session:**

```
🧪 OPERATING MODE TEST MODE
⚠️  WARNING: Only use this on a test system - changes may affect operation!

Enter mode value to test (0-255, 'q' to quit, 'r' to read current): 3
🔄 Attempting to write 3 to Operating Mode register...
✅ Write successful!
🎉 NEW MODE DISCOVERED: 3

Enter mode value to test: 5
❌ Write failed: ExceptionResponse(function_code=134, exception_code=3)
   Exception Code: 3 - Illegal Data Value
```

### 🗺️ Map Mode - Discover Available Registers

Scan register ranges to find all available data:

```bash
python modbus_test.py 192.168.1.80 502 -m
```

**Interactive Range Selection:**

```
🎯 Register Range Selection:
Enter register range to scan, or press Enter for full scan (0-255)
Start register (default 0): 100
End register (default 255): 120
```

**Example Output:**

```
🔍 MODBUS REGISTER SCAN MODE
==============================================================================================
Register   Raw Value    Hex      Name/Temps                    Notes
----------------------------------------------------------------------------------------------
100        8            0x0008   Mode 8                        Could be operating mode or status code
101        80           0x0050   Tank Top Temperature (T5U)    Top of tank temperature
102        154          0x009A   Tank Bottom Temperature (T5L) Bottom of tank temperature
105        27           0x001B   Exhaust Gas Temperature (Tp)  Compressor exhaust temperature
107        480          0x01E0   225.0°C/27.0°C/48.0°C        Possible temperature formulas: Raw: 225.0°C, Scale+Offset: 27.0°C...
120        0            0x0000   Zero                          Could be Off/Disabled state
----------------------------------------------------------------------------------------------
Successfully read 15/21 registers
```

## 🎛️ Command Line Options


| Option | Long Form | Description                            | Example |
| -------- | ----------- | ---------------------------------------- | --------- |
| `-s`   | `--slave` | Modbus slave ID (default: 1)           | `-s 2`  |
| `-t`   | `--test`  | Enable test mode for discovering modes | `-t`    |
| `-m`   | `--map`   | Enable map mode for register scanning  | `-m`    |

## 📖 Understanding the Output

### 🌡️ Temperature Processing

The script applies the correct scaling formulas based on known scaling & offset values for some systems:

* **With scaling** : `result = (raw_value × 0.5) - 15`
* **Without scaling** : `result = raw_value` (like register 105)

### 🔍 Temperature Detection in Map Mode

For unknown registers, the script tests multiple formulas:


| Formula          | Calculation         | Typical Use                 |
| ------------------ | --------------------- | ----------------------------- |
| **Raw**          | `raw_value`         | Direct temperature readings |
| **Scale+Offset** | `(raw × 0.5) - 15` | Most temperature sensors    |
| **Scale×0.1**   | `raw × 0.1`        | Some scaled sensors         |
| **Offset-40**    | `raw - 40`          | Temperature with offset     |

### ⚠️ Error Codes

Common Modbus exception codes you might encounter:


| Code | Name                 | Meaning                                 |
| ------ | ---------------------- | ----------------------------------------- |
| 1    | Illegal Function     | Function code not supported             |
| 2    | Illegal Data Address | Register address doesn't exist          |
| 3    | Illegal Data Value   | Value not allowed (common in test mode) |
| 4    | Slave Device Failure | Device hardware error                   |

## 🏠 Integration with Home Assistant

### Known Register Mappings

The script includes mappings for these known Midea water heater registers:

```yaml
# Control registers
- address: 0   # Power State (0=OFF, 1=ON)
- address: 1   # Operating Mode (1=Eco, 2=Hybrid, 4=E-Heater)
- address: 2   # Target Temperature (°C)

# Temperature sensors (with scaling: raw × 0.5 - 15)
- address: 101 # Tank Top Temperature (T5U)
- address: 102 # Tank Bottom Temperature (T5L) 
- address: 103 # Condensor Temperature (T3)
- address: 104 # Outdoor Temperature (T4)
- address: 106 # Suction Temperature (Th)

# Raw temperature (no scaling)
- address: 105 # Exhaust Gas Temperature (Tp)
```

## 🔧 Troubleshooting

### Connection Issues

* **"Failed to connect"** : Check IP address, port, and network connectivity
* **Timeout errors** : Device may be busy or network latency is high

### Register Read Failures

* **"Illegal Data Address"** : Register doesn't exist on this device
* **"Slave Device Failure"** : Hardware issue with the heat pump

### Test Mode Issues

* **"Illegal Data Value"** : The mode value you're testing isn't supported
* **Write successful but no change** : Device may ignore invalid modes

## 🤝 Contributing

Found new operating modes or register mappings? Please contribute back to the community:

1. **Document your findings** : Note what each mode/register does on your heat pump display
2. **Report discoveries** : Create an issue at [Midea Heat Pump HA Integration](https://github.com/0xAHA/Midea-Heat-Pump-HA/issues)
3. **Include details** : Model number, firmware version, and register behavior

## ⚡ Quick Reference

```bash
# Monitor status
python modbus_test.py 192.168.1.80 502

# Test new operating modes
python modbus_test.py 192.168.1.80 502 -t

# Discover available registers  
python modbus_test.py 192.168.1.80 502 -m

# Custom slave ID
python modbus_test.py 192.168.1.80 502 -s 2

# Help
python modbus_test.py --help
```

## 🚨 Safety Notes

* **Test Mode** : Only use on systems where temporary mode changes are safe
* **Backup Settings** : Note current heat pump settings before testing
* **Monitor Operation** : Watch your heat pump during tests to ensure normal operation
* **Stop if Issues** : If the heat pump behaves unexpectedly, stop testing immediately

---

*This script is designed to help the Home Assistant and water heat pump community discover and document register mappings. Always test safely and contribute your findings back to help others!*
