# VinFast Connected Car for Home Assistant

![VinFast Logo](images/logo.png)

This custom component integrates **VinFast** vehicles into Home Assistant options for monitoring your car's status, including battery level, range, tire pressure, and more.

> **Note**: This integration focuses purely on tracking vehicle status through the VinFast app API. It does not include OCPP/Charging Station features.

## Supported Models
- **VF e34**
- **VF 3**
- **VF 5**
- **VF 6**
- **VF 7**
- **VF 8**
- **VF 9**

## Automated Dashboard Setup (Recommended)

We provide a universal setup script that supports ALL VinFast models and can generate both a full dashboard and a simple card configuration for you.

1.  **Run the configuration wizard:**
    ```bash
    python3 setup_dashboard.py
    ```
2.  **Follow the prompts:**
    *   Enter your entity prefix (e.g., `vf8`, `my_car`, `vinfast`).
    *   Choose between **Full Dashboard** (Wall Panel) or **Simple Card**.
3.  **Copy & Paste:** The script will generate a YAML file. Simply copy its content into Home Assistant.

## Installation via HACS

1.  Open **HACS** in Home Assistant.
2.  Go to **Integrations**.
3.  Click the three dots in the top right corner and select **Custom repositories**.
4.  Paste the URL of this repository.
5.  Select **Integration** as the category.
6.  Click **Add** and then install "VinFast Connected Car".
7.  Restart Home Assistant.

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration** and search for **VinFast**.
3.  Enter your VinFast account credentials (email and password) and select your region.
4.  Your vehicle(s) will be discovered and added as devices.

## Dashboard Options

### Option 1: Full Wall Panel Dashboard
A clear, glassmorphism-style dashboard perfect for wall-mounted tablets.
*   Run `python3 setup_dashboard.py` and select Option 1.
*   Requires `button-card`, `layout-card`, and `card-mod` from HACS.

### Option 2: Simple Card
A comprehensive single card view to add to your existing dashboard.
*   Run `python3 setup_dashboard.py` and select Option 2.

- **Sensors**: Battery, Range, Charging Status, Odometer, Tire Pressures, Temperatures, etc.
- **Binary Sensors**: Doors, Locks, Trunk, Hood.
- **Switch**: Climate Control (Requires pairing).

## Credits
Based on the work of the VinFast Owners community.
