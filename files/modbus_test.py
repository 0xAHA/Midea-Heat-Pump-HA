#!/usr/bin/env python3
"""
Water Heat Pump Modbus Reader
Usage: python modbus_test.py <ip_address> <port> [options]

Modes:
  Default: Read known water heater registers
  -t: Test mode for discovering operating modes  
  -m: Map mode to scan for available registers

Example: python modbus_test.py 192.168.1.80 502 -m
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

def test_operating_modes(client):
    """Interactive test mode for discovering operating modes"""
    print("\n" + "="*60)
    print("🧪 OPERATING MODE TEST MODE")
    print("="*60)
    print("This will attempt to write values to the Operating Mode register (address 1)")
    print("to discover undocumented modes.")
    print("⚠️  WARNING: Only use this on a test system - changes may affect operation!")
    print("-"*60)
    
    mode_register = 1
    test_results = []
    
    while True:
        try:
            user_input = input("\nEnter mode value to test (0-255, 'q' to quit, 'r' to read current): ").strip().lower()
            
            if user_input == 'q':
                break
            elif user_input == 'r':
                # Read current mode
                try:
                    result = client.read_holding_registers(address=mode_register, count=1)
                    if result.isError():
                        print(f"❌ Read error: {result}")
                    else:
                        current_mode = result.registers[0]
                        mode_map = {1: "Eco", 2: "Hybrid", 4: "E-Heater"}
                        mode_name = mode_map.get(current_mode, "Other")
                        print(f"📖 Current mode: {current_mode} ({mode_name})")
                except Exception as e:
                    print(f"❌ Exception reading mode: {e}")
                continue
            
            # Parse the input value
            try:
                test_value = int(user_input)
                if not (0 <= test_value <= 255):
                    print("❌ Value must be between 0 and 255")
                    continue
            except ValueError:
                print("❌ Please enter a valid number, 'r' to read, or 'q' to quit")
                continue
            
            print(f"🔄 Attempting to write {test_value} to Operating Mode register...")
            
            # Attempt to write the value
            write_success = False
            write_error = None
            
            try:
                write_result = client.write_register(address=mode_register, value=test_value)
                
                if write_result.isError():
                    write_error = str(write_result)
                    print(f"❌ Write failed: {write_result}")
                    
                    # Try to decode common Modbus exception codes
                    if hasattr(write_result, 'exception_code'):
                        exception_codes = {
                            1: "Illegal Function",
                            2: "Illegal Data Address", 
                            3: "Illegal Data Value",
                            4: "Slave Device Failure",
                            5: "Acknowledge",
                            6: "Slave Device Busy"
                        }
                        code_name = exception_codes.get(write_result.exception_code, f"Unknown ({write_result.exception_code})")
                        print(f"   Exception Code: {write_result.exception_code} - {code_name}")
                        write_error = f"Exception {write_result.exception_code}: {code_name}"
                else:
                    write_success = True
                    print("✅ Write successful!")
                    
                    # Read back to verify
                    print("🔍 Reading back to verify...")
                    read_result = client.read_holding_registers(address=mode_register, count=1)
                    if read_result.isError():
                        print(f"❌ Readback failed: {read_result}")
                    else:
                        actual_value = read_result.registers[0]
                        if actual_value == test_value:
                            print(f"✅ Verified: Mode is now {actual_value}")
                            mode_map = {1: "Eco", 2: "Hybrid", 4: "E-Heater"}
                            if actual_value not in mode_map:
                                print(f"🎉 NEW MODE DISCOVERED: {actual_value}")
                                print("   Please check your heat pump display and document what this mode does!")
                        else:
                            print(f"⚠️  Value changed to {actual_value} (not {test_value} as requested)")
            
            except Exception as e:
                write_error = str(e)
                print(f"❌ Exception during write: {e}")
            
            # Record the test result
            test_results.append({
                'value': test_value,
                'success': write_success,
                'error': write_error
            })
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Test mode interrupted by user")
            break
        except EOFError:
            print("\n\n⏹️  Test mode ended")
            break
    
    # Summary of test results
    if test_results:
        print(f"\n📊 TEST SUMMARY ({len(test_results)} attempts)")
        print("-"*50)
        successful_writes = []
        failed_writes = []
        
        for result in test_results:
            if result['success']:
                successful_writes.append(result['value'])
                print(f"✅ Mode {result['value']}: SUCCESS")
            else:
                failed_writes.append(result)
                print(f"❌ Mode {result['value']}: {result['error']}")
        
        if successful_writes:
            print(f"\n🎉 Successfully wrote modes: {', '.join(map(str, successful_writes))}")
            print("   Please document what each mode does on your heat pump display!")
            print("   Consider reporting findings at: https://github.com/0xAHA/Midea-Heat-Pump-HA/issues")
        
        if failed_writes:
            print(f"\n❌ Failed attempts: {len(failed_writes)}")
            common_errors = {}
            for fail in failed_writes:
                error = fail['error'] or 'Unknown error'
                common_errors[error] = common_errors.get(error, 0) + 1
            for error, count in common_errors.items():
                print(f"   {error}: {count} occurrence(s)")

def get_known_register_info(address):
    """Get information about known water heater registers"""
    for reg in WATER_HEATER_REGISTERS:
        if reg["address"] == address:
            return reg
    return None

def scan_modbus_registers(client, start_reg=0, end_reg=255):
    """Scan a range of Modbus registers to discover available data"""
    print("\n" + "="*94)
    print("🔍 MODBUS REGISTER SCAN MODE")
    print("="*94)
    print(f"Scanning registers {start_reg} to {end_reg} for available data...")
    print("⚠️  This may take a while depending on the range!")
    print("-"*94)
    
    successful_reads = []
    failed_count = 0
    total_registers = end_reg - start_reg + 1
    
    print(f"{'Register':<10} {'Raw Value':<12} {'Hex':<8} {'Name/Temps':<25}     {'Notes'}")
    print("-"*94)
    
    # Progress tracking
    progress_interval = max(1, total_registers // 20)  # Show progress every 5%
    
    for i, reg_addr in enumerate(range(start_reg, end_reg + 1)):
        # Show progress for large scans
        if total_registers > 50 and (i % progress_interval == 0 or i == total_registers - 1):
            progress = (i + 1) / total_registers * 100
            print(f"Progress: {progress:.0f}% ({i+1}/{total_registers} registers)", end='\r', flush=True)
        
        try:
            result = client.read_holding_registers(address=reg_addr, count=1)
            
            if result.isError():
                failed_count += 1
                continue
                
            raw_value = result.registers[0]
            hex_value = f"0x{raw_value:04X}"
            
            # Check if this is a known register
            known_reg = get_known_register_info(reg_addr)
            
            if known_reg:
                # This is a known register - show the known name
                display_name = known_reg["name"]
                notes = known_reg["description"]
            else:
                # Unknown register - try temperature interpretations
                temp_formulas = [
                    {"name": "Raw", "calc": raw_value, "range": (0, 150)},
                    {"name": "Scale+Offset", "calc": (raw_value * 0.5) - 15, "range": (-20, 120)},
                    {"name": "Scale×0.1", "calc": raw_value * 0.1, "range": (0, 150)},
                    {"name": "Offset-40", "calc": raw_value - 40, "range": (-40, 100)},
                ]
                
                # Find valid temperature interpretations
                valid_temps = []
                temp_details = []
                for formula in temp_formulas:
                    calc_temp = formula["calc"]
                    min_temp, max_temp = formula["range"]
                    if min_temp <= calc_temp <= max_temp:
                        valid_temps.append(f"{calc_temp:.1f}°C")
                        temp_details.append(f"{formula['name']}: {calc_temp:.1f}°C")
                
                if valid_temps:
                    # Show possible temperature values
                    display_name = "/".join(valid_temps[:3])  # Show max 3 interpretations
                    notes = f"Possible temperature formulas: {', '.join(temp_details)}"
                else:
                    # Not a temperature - classify the value
                    if raw_value == 0:
                        display_name = "Zero"
                        notes = "Could be Off/Disabled state"
                    elif raw_value == 1:
                        display_name = "Boolean"
                        notes = "Could be On/Enabled state" 
                    elif 1 < raw_value <= 10:
                        display_name = f"Mode {raw_value}"
                        notes = "Could be operating mode or status code"
                    elif raw_value > 1000:
                        display_name = "Large value"
                        notes = f"Large numeric value - could be counter, timestamp, or scaled measurement"
                    else:
                        display_name = f"Value {raw_value}"
                        notes = "Unknown purpose - monitor for changes during operation"
            
            # Clear progress line and show result
            if total_registers > 50:
                print(' ' * 64, end='\r')  # Clear progress line
            print(f"{reg_addr:<10} {raw_value:<12} {hex_value:<8} {display_name:<25}     {notes}")
            
            successful_reads.append({
                'address': reg_addr,
                'raw_value': raw_value,
                'is_known': known_reg is not None,
                'display_name': display_name,
                'notes': notes
            })
            
        except Exception as e:
            failed_count += 1
            continue
    
    # Summary
    print("-"*94)
    print(f"📊 SCAN SUMMARY")
    print(f"Total registers scanned: {total_registers}")
    print(f"Successful reads: {len(successful_reads)}")
    print(f"Failed/unreadable registers: {failed_count}")
    print(f"Success rate: {len(successful_reads)/total_registers*100:.1f}%")
    
    if successful_reads:
        # Analyze results
        known_registers = [r for r in successful_reads if r['is_known']]
        unknown_registers = [r for r in successful_reads if not r['is_known']]
        potential_temps = [r for r in unknown_registers if '°C' in r['display_name']]
        
        print(f"\nKnown water heater registers found: {len(known_registers)}")
        if known_registers:
            for reg in known_registers:
                print(f"  Register {reg['address']}: {reg['display_name']}")
        
        print(f"\nUnknown registers with potential temperature readings: {len(potential_temps)}")
        if potential_temps:
            for temp_reg in potential_temps[:8]:  # Show first 8
                print(f"  Register {temp_reg['address']}: {temp_reg['display_name']} (raw: {temp_reg['raw_value']})")
            if len(potential_temps) > 8:
                print(f"  ... and {len(potential_temps) - 8} more")
        
        # Look for clusters of registers (likely related data)
        print(f"\nRegister clusters (consecutive readable registers):")
        addresses = [r['address'] for r in successful_reads]
        addresses.sort()
        
        clusters = []
        current_cluster = [addresses[0]]
        
        for i in range(1, len(addresses)):
            if addresses[i] == addresses[i-1] + 1:
                current_cluster.append(addresses[i])
            else:
                if len(current_cluster) >= 3:  # Only show clusters of 3+ registers
                    clusters.append(current_cluster)
                current_cluster = [addresses[i]]
        
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)
            
        for cluster in clusters[:5]:  # Show first 5 clusters
            print(f"  Registers {cluster[0]}-{cluster[-1]} ({len(cluster)} consecutive registers)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print("- Known registers are labeled with their actual function")
        print("- Temperature interpretations show: Raw value / (Raw×0.5)-15 / Raw×0.1 / Raw-40")
        print("- Compare calculated temperatures with your heat pump's display")
        print("- Monitor unknown registers during heat pump operation to understand their purpose")
        print("- Consecutive register blocks often contain related sensor data")

def get_scan_range():
    """Get register range from user input"""
    print("\n🎯 Register Range Selection:")
    print("Enter register range to scan, or press Enter for full scan (0-255)")
    
    try:
        start_input = input("Start register (default 0): ").strip()
        start_reg = int(start_input) if start_input else 0
        
        end_input = input("End register (default 255): ").strip()  
        end_reg = int(end_input) if end_input else 255
        
        # Validate range
        if start_reg < 0 or end_reg < 0:
            print("❌ Register addresses must be >= 0")
            return None, None
            
        if start_reg > end_reg:
            print("❌ Start register must be <= end register")
            return None, None
            
        if end_reg > 65535:
            print("❌ Register addresses must be <= 65535") 
            return None, None
            
        register_count = end_reg - start_reg + 1
        if register_count > 1000:
            confirm = input(f"⚠️  Scanning {register_count} registers may take several minutes. Continue? (y/n): ").lower()
            if confirm != 'y':
                return None, None
                
        return start_reg, end_reg
        
    except ValueError:
        print("❌ Please enter valid numbers")
        return None, None
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Scan cancelled")
        return None, None

def read_water_heater_registers(host, port, slave_id=1, test_mode=False, map_mode=False):
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
        
        # Enter test mode if requested
        if test_mode and success_count > 0:
            test_operating_modes(client)
        
        # Enter map mode if requested (allow even if main registers failed)
        if map_mode:
            start_reg, end_reg = get_scan_range()
            if start_reg is not None and end_reg is not None:
                scan_modbus_registers(client, start_reg, end_reg)
        
        return success_count > 0 or map_mode  # Consider map mode successful even if main registers failed
            
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
  python modbus_test.py 192.168.1.80 502 -t    (enable test mode)
  python modbus_test.py 192.168.1.80 502 -m    (enable map/scan mode)
        """
    )
    
    parser.add_argument('host', help='IP address of water heater')
    parser.add_argument('port', type=int, help='Port number (typically 502)')
    parser.add_argument('-s', '--slave', type=int, default=1, help='Slave ID (default: 1)')
    parser.add_argument('-t', '--test', action='store_true', help='Enable test mode to write values to operating mode register')
    parser.add_argument('-m', '--map', action='store_true', help='Enable map mode to scan for available registers')
    
    # Handle case where no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (1 <= args.port <= 65535):
        print("❌ Error: Port must be between 1 and 65535")
        sys.exit(1)
    
    # Prevent using both test and map mode together
    if args.test and args.map:
        print("❌ Error: Cannot use both test (-t) and map (-m) modes simultaneously")
        print("   Run them separately for best results")
        sys.exit(1)
    
    success = read_water_heater_registers(args.host, args.port, args.slave, args.test, args.map)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()