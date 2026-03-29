#!/usr/bin/env python3
"""
VinFast frontend onboarding wizard for Home Assistant.

This script:
1. Copies bundled custom-card assets to /config/www/vinfast
2. Tries to auto-detect your VinFast entity prefix from HA entity registry
3. Generates Lovelace resource and card/view snippets for quick setup
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WWW_DIR = "/config/www/vinfast"
ENTITY_REGISTRY_PATH = "/config/.storage/core.entity_registry"
ASSET_FILES = [
    "vinfast-digital-twin.js",
    "vinfast-debug-card.js",
    "logo.png",
    "icon.png",
]


def print_header() -> None:
    print("\n" + "=" * 64)
    print("  VinFast Dashboard Setup Wizard")
    print("  For the MQTT / Digital Twin integration build")
    print("=" * 64)
    print("\nThis wizard will copy the frontend files and generate Lovelace snippets.")
    print("It does not touch your Home Assistant storage files automatically.\n")


def prompt(text: str, default: str | None = None, required: bool = False) -> str:
    while True:
        if default is not None:
            value = input(f"{text} (Default: {default}): ").strip()
            if not value:
                value = default
        else:
            value = input(f"{text}: ").strip()
        if value or not required:
            return value
        print("  This field is required.")


def detect_prefixes() -> list[str]:
    if not os.path.exists(ENTITY_REGISTRY_PATH):
        return []
    try:
        with open(ENTITY_REGISTRY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        prefixes = []
        for item in data.get("data", {}).get("entities", []):
            entity_id = item.get("entity_id", "")
            if entity_id.startswith("sensor.") and entity_id.endswith("_trang_thai_hoat_dong"):
                prefix = entity_id.replace("sensor.", "").replace("_trang_thai_hoat_dong", "")
                if prefix not in prefixes:
                    prefixes.append(prefix)
        return prefixes
    except Exception:
        return []


def choose_prefix() -> str:
    detected = detect_prefixes()
    if len(detected) == 1:
        print(f"Detected entity prefix: {detected[0]}")
        use_detected = prompt("Use this prefix? [Y/n]", default="Y")
        if use_detected.lower() in ("", "y", "yes"):
            return detected[0]
    elif detected:
        print("\nDetected these VinFast prefixes:")
        for idx, prefix in enumerate(detected, start=1):
            print(f"{idx}. {prefix}")
        selection = prompt("Choose a prefix number, or press Enter to type manually", default="")
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(detected):
                return detected[index]

    print("\nHow to find the prefix manually:")
    print("1. Open Home Assistant > Settings > Devices & Services > VinFast")
    print("2. Open your vehicle device")
    print("3. Look for an entity like: sensor.vf8_<vin>_trang_thai_hoat_dong")
    print("4. The prefix is everything after 'sensor.' and before the last suffix")
    print("   Example: vf8_abc123xyz\n")
    return prompt("Enter your entity prefix", required=True)


def copy_assets(target_dir: str) -> list[str]:
    os.makedirs(target_dir, exist_ok=True)
    copied = []
    for filename in ASSET_FILES:
        src = os.path.join(SCRIPT_DIR, filename)
        dst = os.path.join(target_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied.append(dst)
    return copied


def build_resource_snippet(version: str) -> str:
    return (
        "# Add these in Settings > Dashboards > Resources\n"
        f"- url: /local/vinfast/vinfast-digital-twin.js?v={version}\n"
        "  type: module\n"
        f"- url: /local/vinfast/vinfast-debug-card.js?v={version}\n"
        "  type: module\n"
    )


def build_stack_snippet(prefix: str) -> str:
    return (
        "type: vertical-stack\n"
        "cards:\n"
        "  - type: custom:vinfast-digital-twin\n"
        "  - type: custom:vinfast-debug-card\n"
        f"    entity: sensor.{prefix}_system_debug_raw\n"
    )


def build_view_snippet(prefix: str) -> str:
    return (
        "title: VinFast\n"
        "path: vinfast\n"
        "icon: mdi:car-electric\n"
        "cards:\n"
        "  - type: custom:vinfast-digital-twin\n"
        "  - type: custom:vinfast-debug-card\n"
        f"    entity: sensor.{prefix}_system_debug_raw\n"
    )


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> int:
    print_header()

    prefix = choose_prefix()
    target_dir = prompt("Where should the frontend assets be copied", default=DEFAULT_WWW_DIR, required=True)

    print("\nChoose output mode:")
    print("1. Dedicated dashboard view")
    print("2. Card stack for an existing dashboard")
    mode = prompt("Enter choice (1 or 2)", default="2", required=True)
    if mode not in ("1", "2"):
        print("Invalid choice.")
        return 1

    copied = copy_assets(target_dir)
    version = datetime.now().strftime("%Y%m%d%H%M%S")

    cwd = os.getcwd()
    resources_path = os.path.join(cwd, "my_vinfast_resources.yaml")
    snippet_path = os.path.join(
        cwd,
        "my_vinfast_view.yaml" if mode == "1" else "my_vinfast_cards.yaml",
    )
    notes_path = os.path.join(cwd, "my_vinfast_setup_notes.txt")

    write_file(resources_path, build_resource_snippet(version))
    if mode == "1":
        write_file(snippet_path, build_view_snippet(prefix))
    else:
        write_file(snippet_path, build_stack_snippet(prefix))

    notes = [
        "VinFast frontend onboarding complete.",
        "",
        "Copied files:",
        *[f"- {path}" for path in copied],
        "",
        "Next steps:",
        "1. Open Home Assistant > Settings > Dashboards > Resources",
        "2. Add the two resource entries from my_vinfast_resources.yaml",
        "3. Refresh the browser fully after adding resources",
        "4. Add a new dashboard view or manual card and paste the generated YAML snippet",
        "",
        "Generated files:",
        f"- {resources_path}",
        f"- {snippet_path}",
        "",
        f"Detected entity prefix: {prefix}",
        f"Debug card entity: sensor.{prefix}_system_debug_raw",
    ]
    write_file(notes_path, "\n".join(notes) + "\n")

    print("\n" + "=" * 64)
    print("Done")
    print("=" * 64)
    print(f"\nEntity prefix: {prefix}")
    print(f"Copied assets to: {target_dir}")
    print(f"Resource snippet: {resources_path}")
    print(f"Dashboard snippet: {snippet_path}")
    print(f"Setup notes: {notes_path}")
    print("\nImportant:")
    print("- Add the JS files as Lovelace resources before adding the custom cards.")
    print("- The Digital Twin card auto-detects your vehicle entities.")
    print(f"- The Debug card uses: sensor.{prefix}_system_debug_raw")
    return 0


if __name__ == "__main__":
    sys.exit(main())
