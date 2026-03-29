# VinFast Connected Car for Home Assistant

[**🇻🇳 Đọc tài liệu bằng tiếng Việt**](README_vi.md)

![VinFast Logo](images/logo.png)

This custom component integrates **VinFast** vehicles into Home Assistant for monitoring, remote actions, trip analytics, charging history, and a bundled Digital Twin dashboard experience.

> **Note**: This build now uses the MQTT/WebSocket implementation and bundled custom-card assets. The old YAML dashboard templates are no longer used.

## Supported Models

- **VF e34**
- **VF 3**
- **VF 5**
- **VF 6**
- **VF 7**
- **VF 8**
- **VF 9**

## 🏁 Beginner's Guide: Dashboard Setup

If you are new to Home Assistant, follow these steps to get the integration and dashboard working quickly.

### Step 1: Install Requirements

Before running the setup wizard, make sure you have:

1. **Terminal & SSH** add-on

   * Go to **Settings > Add-ons > Add-on Store**.
   * Install **Terminal & SSH** and start it.
   * Optional: enable **Show in sidebar**.

2. **HACS**

   * If you do not have HACS yet, install it from `https://get.hacs.xyz`.
   * Restart Home Assistant after installation.

3. **This integration via HACS**

   * Open **HACS > Integrations**.
   * Click the 3 dots > **Custom repositories**.
   * Add this repository URL: `https://github.com/leolionart/vinfast`
   * Select **Integration**.
   * Install **VinFast Connected Car**.
   * Restart Home Assistant.

### Step 2: Configure the Integration

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **VinFast**.
3. Enter your VinFast account email, password, and region.
4. Optional AI fields:

   * **AI Base URL**: any OpenAI-compatible provider, for example `https://api.openai.com/v1`
   * **AI API Key**
   * **AI Model**: for example `gpt-4o-mini`

After setup, the integration will create sensors and buttons with IDs like:

- `sensor.vf8_<vin>_trang_thai_hoat_dong`
- `button.vf8_<vin>_khoa_cua`
- `device_tracker.vf8_<vin>_vi_tri_gps`

## Step 3: Run the Frontend Setup Wizard

This repository now includes the frontend files directly. The wizard copies them into `/config/www/vinfast` and generates the snippets you need.

1. Open **Terminal**.
2. Go to the integration folder:

```bash
cd /config/custom_components/vinfast
```

3. Run the wizard:

```bash
python3 setup_dashboard.py
```

What the wizard does:

- Copies `vinfast-digital-twin.js` and `vinfast-debug-card.js` to `/config/www/vinfast`
- Tries to auto-detect your VinFast entity prefix from Home Assistant
- Generates:
  - `my_vinfast_resources.yaml`
  - `my_vinfast_cards.yaml` or `my_vinfast_view.yaml`
  - `my_vinfast_setup_notes.txt`

## Step 4: Add the Frontend Resources

1. Open **Settings > Dashboards > Resources**.
2. Add the two URLs generated in `my_vinfast_resources.yaml`.

They will look like:

```yaml
- url: /local/vinfast/vinfast-digital-twin.js?v=...
  type: module
- url: /local/vinfast/vinfast-debug-card.js?v=...
  type: module
```

3. Refresh the browser fully after adding resources.

## Step 5: Add the Dashboard Card

You have two options:

### Option 1: Dedicated View

Use the generated `my_vinfast_view.yaml` as a full dashboard view.

### Option 2: Existing Dashboard

Use the generated `my_vinfast_cards.yaml` as a manual card inside an existing dashboard.

The Digital Twin card auto-detects your vehicle entities. The Debug card uses:

```yaml
entity: sensor.<your_prefix>_system_debug_raw
```

## Features

- Real-time MQTT/WebSocket vehicle telemetry
- Remote action buttons
- Trip history and route replay
- Nearby charging stations
- Charging analytics and cost estimation
- Optional AI driving advice using an OpenAI-compatible API
- Bundled Digital Twin and Debug custom cards

## Notes on AI

The AI feature is optional and does **not** affect vehicle connectivity.

You can use:

- OpenAI
- OpenRouter
- Azure-compatible OpenAI gateways
- Local or self-hosted OpenAI-compatible providers

As long as the provider supports a `chat/completions` style API.

## Disclaimer

This project is developed by the open-source community and is not officially certified by or affiliated with VinFast Auto.

All remote actions and telemetry access rely on internal VinFast app APIs and related backend services. Use at your own risk.
