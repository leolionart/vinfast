# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [2026-03-29 MQTT Migration Update]

### Added
- Added MQTT/WebSocket-based VinFast integration implementation imported from the upstream realtime project.
- Added support for OpenAI-compatible AI configuration with `AI Base URL`, `AI API Key`, and `AI Model`.
- Added `setup_dashboard.py` onboarding wizard for copying frontend assets and generating Lovelace snippets.
- Added `UPSTREAM_SOURCE.md` to record the imported upstream repository and commit.
- Added support for `entity_prefix` and `entityPrefix` in the `vinfast-digital-twin` custom card.

### Changed
- Replaced the original polling-based backend implementation with the MQTT/WebSocket architecture.
- Reworked onboarding documentation in both English and Vietnamese to match the current integration behavior.
- Switched the AI advisor from Gemini-specific configuration to OpenAI-compatible `chat/completions` APIs.
- Updated dashboard setup guidance to use bundled frontend assets and generated resource snippets instead of the old YAML template flow.

### Fixed
- Fixed Digital Twin card configuration so `entity_prefix` is no longer ignored.
- Fixed onboarding mismatch between README instructions and the current frontend/dashboard setup flow.
- Fixed AI provider coupling by removing the hard dependency on Gemini-specific API endpoints.

### Removed
- Removed the old polling coordinator flow and related legacy modules from active use.
- Removed the old dashboard template-based setup path from documentation.
- Removed the old Gemini-only AI setup flow.

### Breaking Changes
- The integration no longer uses the previous polling-based architecture.
- Old dashboard YAML templates are no longer part of the active setup path.
- Existing Gemini configuration is not used by the new AI configuration flow and must be re-entered if AI features are desired.
- Frontend custom cards must be loaded as Lovelace resources before using `custom:vinfast-digital-twin`.

### Upgrade Notes
- Re-add or reload the VinFast integration if Home Assistant keeps stale entities from the previous architecture.
- If using the Digital Twin card, ensure the frontend JS assets are available under `/local/vinfast/` and added in Lovelace Resources.
- If using AI advisor features, configure:
  - `AI Base URL`
  - `AI API Key`
  - `AI Model`

### Related Commits
- `2ce2f47` Replace integration with MQTT implementation and OpenAI-compatible AI config
- `4c8da0e` Restore friendly docs and add dashboard setup wizard
- `74d22ac` Support entity_prefix in digital twin card
