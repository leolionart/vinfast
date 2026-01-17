# VinFast Climate Control - Future Implementation

## Current Status

Climate control (remote start A/C, defrost, etc.) is **not yet implemented** in this integration.

## Why It's Not Available

Remote climate control requires device-paired cryptographic keys that are unique to each user's phone/vehicle pairing. These keys are generated during the initial app setup process and stored securely on the device.

Unlike read-only telemetry (battery, location, etc.), remote commands require authenticated signing to prevent unauthorized access to vehicle controls.

## Technical Requirements

To implement climate control, the integration would need:

1. **Device-paired keys** - Unique to each user, generated during VinFast app pairing
2. **Cryptographic signing** - Commands must be signed to prove authenticity
3. **Two-factor verification** - VinFast uses QR code + OTP verification for pairing

## Community Status

This is an area of active research in the VinFast owner community. If you're interested in contributing to this effort, please reach out via the community forums.

## Security Note

VinFast's security model for remote commands is designed to protect vehicle owners. Any implementation would need to:

- Respect the existing security architecture
- Only allow authorized users to control their own vehicles
- Not bypass or weaken existing protections

## Related Features (Working)

While climate control is not available, the following **read-only** features work:

- Battery level and range
- Charging status and power
- Vehicle location
- Tire pressures
- Door/window/trunk status
- Odometer
- Temperature readings (inside/outside)

---

*This document is intentionally limited to protect VinFast's security implementation.*
