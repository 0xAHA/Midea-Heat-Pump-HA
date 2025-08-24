#!/usr/bin/env python3
"""
Water Heat Pump Modbus Reader
Usage: python modbus_test.py <ip_address> <port>
Example: python modbus_test.py 192.168.1.80 502
"""

from pymodbus.client import ModbusTcpClient
import sys
import argparse

# Water heat pump register configuration
WATER_HEATER_REGISTERS = [
    # Control registers
    {"address": 0, "name": "Power State", "type": "status", "description": "On/Off Status"},
    {"address": 1, "name": "Operating Mode", "type": "mode", "description": "Heat pump mode"},
    {"address": 2, "name": "Target Temperature", "type": "temperature", "unit": "°C", "description": "Set point temperature"},
    
    # Temperature sensors
    {"address": 101, "name": "Tank Top Temperature (T5U)", "type": "temperature", "unit": "°C", "offset": -15, "scale": 0.5, "description": "Top of tank temperature"},
    {"address": 102, "name": "Tank Bottom Temperature (T5L)", "type": "temperature", "unit": "°C", "offset": -15, "scale": 0.5, "description": "Bottom of tank temperature"},
    {"address": 103, "name": "Condensor Temperature (T3)", "type": "temperature", "unit": "°C", "offset": -15, "scale": 0.5, "description": "Condensor temperature"},
    {"address": 104, "name": "Outdoor Temperature (T4)", "type": "temperature", "unit": "°C", "offset": -15, "scale": 0.5, "description": "Ambient outdoor temperature"},
    {"address": 105, "name": "Exhaust Gas Temperature (Tp)", "type": "temperature", "unit": "°C", "description": "Compressor exhaust temperature"},
    {"address": 106, "name": "Suction Temperature (Th)", "type": "temperature", "unit": "°C", "offset": -15, "scale": 0.5, "description": "Compressor suction temperature"},
]

def process_value(raw_value, register_config):
    """Apply scaling and offset to raw register value"""
    processed = raw_value
    
    # Apply scale first (Home Assistant modbus order)
    if "scale" in register_config:
        processed *= register_config["scale"]
    
    # Then apply offset
    if "offset" in register_config:
        processed += register_config["offset"]
    
    return processed

def format_value(raw_value, register_config):
    """Format the value with appropriate units and precision"""
    processed = process_value(raw_value, register_config)
    
    if register_config["type"] == "temperature":
        if "scale" in register_config:
            return f"{processed:.1f} {register_config.get('unit', '')}"
        else:
            return f"{processed} {register_config.get('unit', '')}"
    elif register_config["type"] == "status":
        return "ON" if processed == 1 else "OFF"
    elif register_config["type"] == "mode":
        # Map heat pump operating modes
        mode_map = {
            1: "Eco",
            2: "Hybrid", 
            4: "E-Heater"
        }
        if processed in mode_map:
            return mode_map[processed]
        else:
            return "Other"
    else:
        return str(processed)

def is_unknown_mode(raw_value, register_config):
    """Check if this is an unknown operating mode"""
    if register_config["type"] == "mode":
        processed = process_value(raw_value, register_config)
        mode_map = {1: "Eco", 2: "Hybrid", 4: "E-Heater"}
        return processed not in mode_map
    return False

def read_water_heater_registers(host, port, slave_id=1):
    """Read all water heater registers and display in a table"""
    
    print(f"🌡️  Water Heat Pump Status - {host}:{port}")
    print("=" * 85)
    
    client = ModbusTcpClient(host=host, port=port)
    
    try:
        client.unit_id = slave_id
    except:
        pass
    
    try:
        if not client.connect():
            print("❌ Failed to connect to water heater")
            return False
        
        print("✅ Connected successfully\n")
        
        # Table header
        print(f"{'Register':<8} {'Name':<35} {'Raw Value':<12} {'Processed Value':<18} {'Description'}")
        print("-" * 85)
        
        success_count = 0
        total_count = len(WATER_HEATER_REGISTERS)
        unknown_modes_found = []
        
        for reg_config in WATER_HEATER_REGISTERS:
            address = reg_config["address"]
            name = reg_config["name"]
            description = reg_config["description"]
            
            try:
                # Read holding register
                result = client.read_holding_registers(address=address, count=1)
                
                if result.isError():
                    print(f"{address:<8} {name:<35} {'ERROR':<12} {'-':<18} {description}")
                    continue
                
                raw_value = result.registers[0]
                formatted_value = format_value(raw_value, reg_config)
                
                # Check for unknown operating modes
                if is_unknown_mode(raw_value, reg_config):
                    processed_value = process_value(raw_value, reg_config)
                    unknown_modes_found.append(processed_value)
                
                # Show raw value in hex if it's useful
                raw_display = f"{raw_value} (0x{raw_value:04X})"
                
                print(f"{address:<8} {name:<35} {raw_display:<12} {formatted_value:<18} {description}")
                success_count += 1
                
            except Exception as e:
                print(f"{address:<8} {name:<35} {'EXCEPTION':<12} {'-':<18} {description}")
                continue
        
        print("-" * 85)
        print(f"Successfully read {success_count}/{total_count} registers")
        
        # Show message about unknown modes if any were found
        if unknown_modes_found:
            print(f"\n⚠️  NOTICE: Found undocumented operating mode(s): {', '.join(map(str, unknown_modes_found))}")
            print("   Please verify the mode on your water heater's display and report it at:")
            print("   https://github.com/0xAHA/Midea-Heat-Pump-HA/issues")
            print("   This will help improve the integration for everyone!")
        
        return success_count > 0
            
    except Exception as e:
        print(f"❌ Connection exception: {e}")
        return False
    finally:
        client.close()
        print("\nConnection closed")

def main():
    parser = argparse.ArgumentParser(
        description='Read Water Heat Pump Modbus registers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python modbus_test.py 192.168.1.80 502
  python modbus_test.py 10.0.0.100 502 -s 2
        """
    )
    
    parser.add_argument('host', help='IP address of water heater')
    parser.add_argument('port', type=int, help='Port number (typically 502)')
    parser.add_argument('-s', '--slave', type=int, default=1, help='Slave ID (default: 1)')
    
    # Handle case where no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Validate port range
    if not (1 <= args.port <= 65535):
        print("❌ Error: Port must be between 1 and 65535")
        sys.exit(1)
    
    success = read_water_heater_registers(args.host, args.port, args.slave)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()