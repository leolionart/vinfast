# VinFast Connected Car Integration for Home Assistant

A custom Home Assistant integration for VinFast electric vehicles that provides real-time telemetry data.

## Features

- Real-time battery level and range
- Charging status and power monitoring
- Vehicle location tracking (device tracker)
- Tire pressure monitoring (all 4 tires)
- Interior and exterior temperature
- Door, window, trunk, and hood status
- Lock status and ignition state
- Odometer with automatic km to miles conversion
- Automatic token refresh

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots menu → **Custom repositories**
4. Add `https://github.com/vinfastownersorg-cyber/vinfastowners` as an Integration
5. Search for "VinFast" and install
6. Restart Home Assistant

### Manual Installation

1. Copy the `vinfast` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "VinFast"
4. Enter your VinFast account email and password
5. The integration will automatically detect your vehicle

---

## Sensors

### Vehicle Information

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.vinfast_odometer` | Odometer | mi | Total distance traveled (converted from km) |
| `sensor.vinfast_vehicle_name` | Vehicle Name | - | Custom or default vehicle name |
| `sensor.vinfast_model` | Model | - | Vehicle type and variant (e.g., "VF8 Plus") |
| `sensor.vinfast_year` | Year | - | Model year |
| `sensor.vinfast_color` | Color | - | Exterior color |
| `sensor.vinfast_vin` | VIN | - | Vehicle Identification Number |

### Battery & Charging

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.vinfast_battery_level` | Battery Level | % | Current state of charge |
| `sensor.vinfast_range` | Range | mi | Estimated range (converted from km) |
| `sensor.vinfast_charging_status` | Charging Status | - | Text status (see table below) |
| `sensor.vinfast_charging_power` | Charging Power | kW | Current charging power |
| `sensor.vinfast_time_to_full` | Time to Full | min | Estimated time to full charge |
| `sensor.vinfast_charge_limit` | Charge Limit | % | Maximum charge limit setting |
| `sensor.vinfast_battery_12v` | 12V Battery | V | Auxiliary battery voltage |

### Driving

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.vinfast_speed` | Speed | mph | Current speed (converted from km/h) |
| `sensor.vinfast_gear` | Gear | - | Current gear position (P/R/N/D) |

### Temperature

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.vinfast_outside_temp` | Outside Temp | °F | Exterior temperature (converted from °C) |
| `sensor.vinfast_inside_temp` | Inside Temp | °F | Interior temperature (converted from °C) |

### Tire Pressure

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.vinfast_tire_pressure_fl` | Tire Pressure FL | PSI | Front left tire (converted from kPa) |
| `sensor.vinfast_tire_pressure_fr` | Tire Pressure FR | PSI | Front right tire (converted from kPa) |
| `sensor.vinfast_tire_pressure_rl` | Tire Pressure RL | PSI | Rear left tire (converted from kPa) |
| `sensor.vinfast_tire_pressure_rr` | Tire Pressure RR | PSI | Rear right tire (converted from kPa) |

---

## Binary Sensors

| Entity ID | Name | On State | Off State | Description |
|-----------|------|----------|-----------|-------------|
| `binary_sensor.vinfast_locked` | Locked | Locked | Unlocked | Vehicle lock status |
| `binary_sensor.vinfast_ignition` | Ignition | On | Off | Ignition/power state |
| `binary_sensor.vinfast_charging` | Charging | Charging | Not Charging | Active charging status |
| `binary_sensor.vinfast_plugged_in` | Plugged In | Plugged | Unplugged | Charge cable connected |
| `binary_sensor.vinfast_trunk_open` | Trunk | Open | Closed | Trunk/liftgate status |
| `binary_sensor.vinfast_hood_open` | Hood | Open | Closed | Front hood status |
| `binary_sensor.vinfast_door_open` | Doors | Open | Closed | Any door open |
| `binary_sensor.vinfast_window_open` | Windows | Open | Closed | Any window open |

---

## Device Tracker

| Entity ID | Description |
|-----------|-------------|
| `device_tracker.vinfast_location` | GPS location of vehicle |

---

## Status Code Reference

### Charging Status (`sensor.vinfast_charging_status`)

| Value | State |
|-------|-------|
| 0 | Not Charging |
| 1 | Charging |
| 2 | Complete |
| 3 | Scheduled |
| 4 | Error |

### Gear Position (`sensor.vinfast_gear`)

| Value | State |
|-------|-------|
| 0 | P (Park) |
| 1 | R (Reverse) |
| 2 | N (Neutral) |
| 3 | D (Drive) |

---

## Unit Conversions

All values are automatically converted from metric (API) to imperial (display):

| Measurement | API Unit | Display Unit | Conversion |
|-------------|----------|--------------|------------|
| Distance | km | miles | × 0.621371 |
| Speed | km/h | mph | × 0.621371 |
| Temperature | °C | °F | (°C × 9/5) + 32 |
| Pressure | kPa | PSI | × 0.145038 |

---

## Limitations

- **Read-only**: This integration provides read-only access to vehicle data
- **No remote commands**: Lock, unlock, climate controls require additional setup (see `docs/CLIMATE_CONTROL_TODO.md`)
- **Update interval**: Data refreshes every 5 minutes to minimize API calls
- **US accounts only**: Currently only supports US VinFast accounts

## Privacy & Security

- Credentials are stored securely in Home Assistant's encrypted config entry
- Communication uses HTTPS encryption
- No data is sent to third parties
- Auth0 client ID is a public identifier (same for all VinFast app users)

## Troubleshooting

### "Invalid credentials" error
- Verify your email and password are correct
- Ensure you can log in to the VinFast mobile app

### "No vehicles found" error
- Make sure you have a vehicle registered to your VinFast account
- The account must be the primary owner of the vehicle

### Sensors show "unavailable"
- Telemetry sensors require the vehicle to have sent recent data
- Check Home Assistant logs for API errors
- Try removing and re-adding the integration

### Odometer not updating
- The integration prefers real-time telemetry data
- Falls back to vehicle info endpoint if telemetry unavailable
- Vehicle info may be cached/stale on VinFast's servers

## Support

For issues and feature requests, please open an issue on GitHub.

## Disclaimer

This is an unofficial community integration and is not affiliated with, endorsed by, or supported by VinFast. Use at your own risk.
