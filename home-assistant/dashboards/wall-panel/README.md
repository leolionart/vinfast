# VinFast EV Wall Panel Dashboard for Home Assistant

A beautiful glassmorphism-style wall panel dashboard designed specifically for VinFast EV owners. Optimized for Google Nest Hub displays (7" and 10") and tablets, with mobile-responsive support for quick status checks on phones.

**Supports 1-4 VinFast vehicles on a single dashboard!**

## Features

### v8 Enhancements (Latest - December 2025)
- **12V Battery Display** - Shows 12V battery level next to odometer
- **OCPP Charging Stats** *(Optional)* - Live charging power, session energy, time to full, and duration
- **Telemetry Status Display** - Shows "Updated Xm ago" and "Next in Xh Xm"
- **Stale Data Warning** - Yellow alert when data is over 5 hours old
- **Manual Refresh Button** - Tap to trigger immediate telemetry update
- **Privacy-Safe Configuration** - Generic entity names for public sharing
- **Optional Integrations Clearly Marked** - OCPP and camera batteries can be easily removed

### v7 Features
- **Combined Time & Weather Card** - Clock and weather unified in a sleek header
- **Live Vehicle Status** - Real-time indicators for gear, lock, plug, and doors
- **Temperature Display** - Both inside and outside temperatures
- **Odometer Reading** - Current mileage display
- **Charge Limit Marker** - Visual indicator on battery bar showing charge limit
- **Charging Animation** - Pulsing effect when charging
- **Conditional Styling** - Status buttons change color based on state

### Core Features
- **12-Hour Clock with AM/PM** - Large, easy-to-read time display
- **Weather Overview** - Current conditions, temperature, humidity, wind
- **VinFast EV Status** - Battery percentage, range, charging status with visual progress bar
- **Vehicle Location Map** - Dark mode map showing your VinFast location
- **EV Savings Tracker** - Track your savings vs gas costs
- **Security Status** - Alarm system and garage door status (display only - no controls)
- **Presence Detection** - Who's home at a glance
- **Battery Monitor** - Phone and camera battery levels
- **Fully Responsive** - Optimized layouts for large displays (4-column), tablets (2-column), and phones (single-column stack)

## Prerequisites

### Home Assistant Requirements

- **Home Assistant** 2024.1 or newer
- **HACS** (Home Assistant Community Store) - [Installation Guide](https://hacs.xyz/docs/setup/download)

### Required Custom Cards (via HACS)

These frontend cards must be installed via HACS before the dashboard will work:

| Card | Purpose | HACS Search |
|------|---------|-------------|
| [button-card](https://github.com/custom-cards/button-card) | Custom styled buttons & cards | "button-card" |
| [layout-card](https://github.com/thomasloven/lovelace-layout-card) | CSS Grid layout support | "layout-card" |
| [card-mod](https://github.com/thomasloven/lovelace-card-mod) | Custom CSS styling | "card-mod" |

### Required Integrations

| Integration | Source | Purpose |
|-------------|--------|---------|
| **VinFast** | This repo (`custom_components/vinfast/`) | Vehicle telemetry (battery, range, location, etc.) |
| **Weather** | HA Built-in | Weather display (Met.no, OpenWeatherMap, etc.) |
| **Mobile App** | HA Built-in | Phone battery & presence detection |
| **Map** | HA Built-in | Vehicle location display |

### Optional Integrations

These can be safely removed from the dashboard if you don't have them:

| Integration | Source | Purpose | How to Remove |
|-------------|--------|---------|---------------|
| **OCPP Charger** | HA OCPP Integration | Live charging stats (power, kWh, duration) | Remove lines 177-186 and 308-327 from YAML |
| Alarm Panel | HA Store or custom | Security status display | Remove alarm panel card section |
| Garage Door | HA Store or custom | Garage door status | Remove garage door elements from security card |
| Camera batteries | Arlo, Ring, etc. | Camera battery monitoring | Remove lines 683-687 and 708-736 from YAML |

## Installation

### Step 1: Install HACS (if not already installed)

HACS is required to install the custom frontend cards.

1. Follow the [official HACS installation guide](https://hacs.xyz/docs/setup/download)
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration** → search "HACS"
4. Complete HACS setup

### Step 2: Install Required Custom Cards

```
1. Open Home Assistant
2. Go to HACS → Frontend
3. Click "+ Explore & Download Repositories"
4. Search and install each card:
   - "button-card" by custom-cards
   - "layout-card" by Thomas Lovén
   - "card-mod" by Thomas Lovén
5. IMPORTANT: Restart Home Assistant after installing all three
6. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)
```

### Step 3: Install VinFast Integration

```
1. Download the `custom_components/vinfast/` folder from this repository
2. Copy it to your Home Assistant `/config/custom_components/` directory
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "VinFast" and enter your account credentials
6. Select your region (US, Europe, or Vietnam)
```

### Step 4: Add Required Images

Create the vinfast folder and add your images:

```
/config/www/vinfast/vf8.png      # Your VinFast vehicle image (transparent PNG)
/config/www/vinfast/vf_bg.png    # Your background image
```

### Step 5: Create the Dashboard

#### Option A: Via UI (Recommended)

1. Go to **Settings** > **Dashboards**
2. Click **Add Dashboard**
3. Name it "Wall Panel" with URL "wall-panel"
4. Open the new dashboard
5. Click the three dots menu > **Edit Dashboard**
6. Click three dots again > **Raw configuration editor**
7. Paste the contents of `vinfast-wall-panel.yaml`
8. Save

#### Option B: Via YAML Mode

Add to your `configuration.yaml`:

```yaml
lovelace:
  mode: storage
  dashboards:
    wall-panel:
      mode: yaml
      title: Wall Panel
      icon: mdi:car-electric
      show_in_sidebar: true
      filename: wall-panel.yaml
```

Then copy `vinfast-wall-panel.yaml` to `/config/wall-panel.yaml`.

### Step 6: Configure Your Entities

#### Option A: Interactive Setup Script (Recommended)

Run the setup script to automatically configure all entity IDs:

```bash
# Download the files
cd ~/Downloads
git clone https://github.com/vinfastownersorg-cyber/vinfastowners.git
cd vinfastowners/home-assistant/dashboards/wall-panel

# Run the setup script
python3 setup.py
```

The script will:
- Ask how many VinFast vehicles you have (1-4)
- Prompt you for each vehicle's entity IDs with examples
- Auto-detect VinFast entity prefix (e.g., `vf8`, `myvf`)
- Generate a unified map showing all vehicle locations
- Automatically adjust the grid layout for your number of vehicles
- Skip optional sections you don't need
- Generate a ready-to-use `my-vinfast-wall-panel.yaml`
- Save your configuration to `my-config.json` for future reference

#### Option B: Manual Configuration

Open the YAML file and replace all entity IDs marked with `# CHANGE:` comments:

```yaml
# VinFast sensors
sensor.vinfast_battery              # Your VinFast battery sensor
sensor.vinfast_range                # Your VinFast range sensor
sensor.vinfast_charge_limit         # Charge limit percentage
sensor.vinfast_charging_status      # "Charging", "Not Charging", etc.
sensor.vinfast_odometer             # Odometer reading
sensor.vinfast_gear                 # Current gear (P/R/N/D)
sensor.vinfast_temperature_outside  # Outside temperature
sensor.vinfast_temperature_inside   # Inside temperature
device_tracker.vinfast_location     # Your VinFast location tracker

# VinFast binary sensors (for status indicators)
binary_sensor.vinfast_locked        # Vehicle lock status
binary_sensor.vinfast_plug          # Charging plug connected
binary_sensor.vinfast_door          # Any door open
binary_sensor.vinfast_charging      # Is actively charging

# Weather & Environment
weather.forecast_home               # Your weather entity

# Security (display only)
alarm_control_panel.home_alarm      # Your alarm panel
binary_sensor.garage_door           # Your garage door sensor

# Presence
person.user_1                       # Your person entities
person.user_2

# Batteries
sensor.phone_1_battery              # Your phone battery sensors
sensor.phone_2_battery
sensor.camera_1_battery             # Your camera battery sensors
sensor.camera_2_battery
sensor.camera_3_battery
sensor.camera_4_battery

# EV Savings (optional - remove section if not using)
sensor.ev_savings_today
sensor.ev_savings_month
sensor.ev_savings_percent
```

## Tire Pressure Color Coding

The dashboard uses color-coded tire pressure indicators:

| Color | Range | Status |
|-------|-------|--------|
| Green | 35-42 PSI | Normal |
| Yellow | 32-35 or 42-45 PSI | Warning |
| Red | <32 or >45 PSI | Danger |

Adjust the thresholds in the YAML if your VinFast model has different recommended pressures.

## Display on Google Nest Hub

### Via Home Assistant Cast

```yaml
# In automations.yaml or via Developer Tools > Services
service: cast.show_lovelace_view
data:
  entity_id: media_player.your_nest_hub
  dashboard_path: wall-panel
  view_path: home
```

## Customization

### Change Background

Replace the background URL in the YAML:

```yaml
background: "center / cover no-repeat fixed url('/local/your-background.jpg')"
```

### Change Temperature Units

Find `°F` in the YAML and replace with `°C` if needed.

### Switch to 24-Hour Time

Replace the time card's JavaScript:

```javascript
const hours = now.getHours().toString().padStart(2, '0');
const mins = now.getMinutes().toString().padStart(2, '0');
// Remove the ampm variable and its display
```

### Remove Sections

Delete any card section you don't need (EV Savings, Battery Status, etc.)

## Troubleshooting

### Cards not rendering
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Ensure all custom cards are installed via HACS
- Restart Home Assistant after installing cards

### Map not showing
- Verify your VinFast device tracker entity exists and has coordinates
- Check that the VinFast integration is properly configured

### Entities showing "unavailable"
- Verify entity IDs match your Home Assistant entities exactly
- Check that integrations are connected and working

### Background not loading
- Ensure the image is in `/config/www/` folder
- Try accessing directly: `http://your-ha:8123/local/vinfast/vf_bg.png`
- Restart Home Assistant after adding new files to www folder

## Security Notes

This dashboard is **display-only** for security items:
- Garage door shows Open/Closed status but cannot control the door
- Alarm shows status but cannot arm/disarm
- No sensitive data is exposed (no IP addresses, tokens, or personal identifiers)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

## Credits

- Dashboard design inspired by modern glassmorphism UI trends
- Built for the VinFast Owners community

## Support

- [VinFast Owners Community](https://vinfastowners.org)
- [Home Assistant Community](https://community.home-assistant.io/)
- [Report Issues](https://github.com/vinfastownersorg-cyber/vinfastowners/issues)

---

Made with love for VinFast owners by the VinFast Owners community
