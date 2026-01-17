#!/usr/bin/env python3
"""
VinFast Dashboard Setup Script (Universal Support)
Supports all VinFast models (VF e34, VF 3, VF 5, VF 6, VF 7, VF 8, VF 9)

This script will:
1. Ask for your VinFast entity prefix (e.g. 'vinfast', 'vf8', 'my_car')
2. Automatically generate a configuration file for your Home Assistant
3. Allow choosing between a full "Wall Panel" dashboard or a "Simple Card"
"""

import os
import sys
import re

# Template paths
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboards", "templates")
WALL_PANEL_TEMPLATE = os.path.join(TEMPLATE_DIR, "wall-panel.yaml")
SIMPLE_CARD_TEMPLATE = os.path.join(TEMPLATE_DIR, "simple-card.yaml")

def print_header():
    print("\n" + "=" * 60)
    print("  VinFast Dashboard Configuration Wizard")
    print("  Supports: VF e34, VF 3, VF 5, VF 6, VF 7, VF 8, VF 9")
    print("=" * 60)
    print("\nThis script will generate a Home Assistant YAML file for you.")
    print("You just need to know your Entity Prefix.\n")
    print("How to find your Entity Prefix:")
    print("1. Go to Home Assistant > Settings > Devices & Services > VinFast")
    print("2. Click on '1 device' (or your vehicle)")
    print("3. Look at an entity ID. Example: if 'sensor.my_vf8_battery', prefix is 'my_vf8'")
    print("-" * 60 + "\n")

def get_input(prompt, default=None):
    """Get user input with default value."""
    if default:
        user_input = input(f"{prompt} (Default: {default}): ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("  This field is required.")

def main():
    print_header()

    # 1. Get Entity Prefix
    prefix = get_input("Enter your VinFast entity prefix", default="vinfast")
    
    # 2. Choose Mode
    print("\nChoose your desired output:")
    print("1. Full Wall Panel Dashboard (Great for tablets/screens)")
    print("2. Simple Card (To add to an existing dashboard)")
    
    while True:
        mode = input("Enter choice (1 or 2): ").strip()
        if mode in ['1', '2']:
            break
        print("Please enter 1 or 2.")

    # 3. Read Template
    if mode == '1':
        template_path = WALL_PANEL_TEMPLATE
        output_name = "my_vinfast_dashboard.yaml"
        print(f"\nUsing template: {template_path}")
    else:
        template_path = SIMPLE_CARD_TEMPLATE
        output_name = "my_vinfast_card.yaml"
        print(f"\nUsing template: {template_path}")

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        print("Please ensure you are running this script from the repository root.")
        sys.exit(1)

    with open(template_path, 'r') as f:
        content = f.read()

    # 4. Process Content
    # The simple card template uses {prefix}
    # The wall panel template likely uses 'vinfast_' or references that need regex replacement
    
    if mode == '2':
        # Simple Card Replacement
        new_content = content.replace("{prefix}", prefix)
        
        # Optional: Ask for car image if it's the card
        default_img = "https://7b50d2de0634f64.cmccloud.com.vn/pasterly/Gemini_Generated_Image_r0xcbkr0xcbkr0xc.png"
        use_custom_img = input(f"\nUse default car image? (y/n): ").strip().lower()
        if use_custom_img == 'n':
             img_url = get_input("Enter URL for your car image")
             new_content = new_content.replace(default_img, img_url)

    else:
        # Wall Panel Replacement
        # This is trickier because the original wall panel yaml might not have standardized {prefix} yet
        # or uses 'sensor.vinfast_' hardcoded.
        # We'll do a smart replace on standard sensor names.
        
        # Common naming pattern in the wall panel yaml: "sensor.vinfast_"
        # We replace "sensor.vinfast_" with "sensor.prefix_"
        # And "binary_sensor.vinfast_" with "binary_sensor.prefix_"
        # And "device_tracker.vinfast_" with "device_tracker.prefix_"
        
        # CAUTION: The user's prefix might ALREADY contain the car model, e.g. "vf8_".
        # If the template expects "sensor.vinfast_battery", and user enters "vf8", 
        # we want "sensor.vf8_battery".
        
        replacements = [
            ("sensor.vinfast_", f"sensor.{prefix}_"),
            ("binary_sensor.vinfast_", f"binary_sensor.{prefix}_"),
            ("device_tracker.vinfast_", f"device_tracker.{prefix}_"),
            # Also handle the 'switch' and 'number' if any exist
            ("switch.vinfast_", f"switch.{prefix}_"),
            ("number.vinfast_", f"number.{prefix}_"),
            # Special case: user says prefix is "vf3", template has "vf8.png"
            # We can try to update the image path too 
            ("/local/vinfast/vf8.png", f"/local/vinfast/{prefix}.png")
        ]
        
        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)

    # 5. Write Output
    output_path = os.path.join(os.getcwd(), output_name)
    with open(output_path, 'w') as f:
        f.write(new_content)

    print("\n" + "=" * 60)
    print("SUCCESS! Generation Complete.")
    print("=" * 60)
    print(f"\nConfiguration saved to: {output_path}")
    print("\nNext Steps:")
    if mode == '1':
        print("1. Open Home Assistant > Settings > Dashboards")
        print("2. Add Dashboard (or edit 'Raw Configuration' of an existing one)")
        print(f"3. Copy/Paste the contents of {output_name}")
    else:
        print("1. Open your Home Assistant Dashboard")
        print("2. Edit Dashboard > Add Card")
        print("3. Scroll down and select 'Manual'")
        print(f"4. Copy/Paste the contents of {output_name}")
        
    print("\nEnjoy your VinFast dashboard!")

if __name__ == "__main__":
    main()
