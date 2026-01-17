# VinFast Connected Car for Home Assistant

[**🇻🇳 Đọc tài liệu bằng tiếng Việt**](README_vi.md)


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

## 🏁 Beginner's Guide: Dashboard Setup

If you are new to Home Assistant, follow these steps to set up a beautiful dashboard for your VinFast car.

### Step 1: Install Requirements

Before running the setup script, you need a few things installed:

1.  **"Terminal & SSH" Add-on** (To run the setup script):
    *   Go to **Settings > Add-ons > Add-on Store**.
    *   Search for "Terminal & SSH".
    *   Click **Install** and then **Start**.
    *   *Tip: Enable "Show in sidebar" for easy access.*

2.  **Custom Cards** (Via HACS - Required for the dashboard to look right):
    *   Go to **HACS > Frontend**.
    *   Click **+ Explore & Download Repositories**.
    *   Search for and install these three cards:
        1.  `button-card`
        2.  `layout-card`
        3.  `card-mod`
    *   **Restart Home Assistant** after installing them.

### Step 2: Run the Setup Wizard

Now we will run a simple script that writes the dashboard code for you.

1.  Open **Terminal** (from the sidebar or Add-ons menu).
2.  Type the following command to go to the plugin folder:
    ```bash
    cd /config/custom_components/vinfast
    ```
3.  Run the setup wizard:
    ```bash
    python3 setup_dashboard.py
    ```
4.  **Follow the on-screen prompts:**
    *   **Entity Prefix**: It will ask for your prefix. (e.g., if your sensor is `sensor.vf8_battery`, type `vf8`).
    *   **Choice**: Type `1` for a Full Wall Panel or `2` for a Simple Card.

### Step 3: Add to Dashboard

1.  The script will tell you it saved a file (e.g., `my_vinfast_dashboard.yaml`).
2.  Open that file (you can use the **File Editor** add-on) and copy all the text.
3.  Go to your **Dashboard**.
4.  Click **Edit Dashboard** (pencil icon).
5.  **For Simple Card**: Click **Add Card** > Scroll down to **Manual** > Paste the text.
6.  **For Wall Panel**: Click only the specific "Raw Configuration Editor" (3 dots > Raw config) if replacing the whole view, OR create a new View and use "Panel" mode.

## Installation via HACS

1. Open **HACS** in Home Assistant.
2. Go to **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Paste the URL of this repository.
5. Select **Integration** as the category.
6. Click **Add** and then install "VinFast Connected Car".
7. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **VinFast**.
3. Enter your VinFast account credentials (email and password) and select your region.
4. Your vehicle(s) will be discovered and added as devices.

## Dashboard Options

### Option 1: Full Wall Panel Dashboard

A clear, glassmorphism-style dashboard perfect for wall-mounted tablets.

* Run `python3 setup_dashboard.py` and select Option 1.
* Requires `button-card`, `layout-card`, and `card-mod` from HACS.

### Option 2: Simple Card

![VinFast Card](https://storage.googleapis.com/prod-omniagent/images/Image-518x752-20260117-032430.png)

A comprehensive single card view to add to your existing dashboard.

* Run `python3 setup_dashboard.py` and select Option 2.

- **Sensors**: Battery, Range, Charging Status, Odometer, Tire Pressures, Temperatures, etc.
- **Binary Sensors**: Doors, Locks, Trunk, Hood.
- **Switch**: Climate Control (Requires pairing).

## Credits

Based on the work of the VinFast Owners community.
