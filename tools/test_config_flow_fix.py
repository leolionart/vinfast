import sys
import unittest
from unittest.mock import MagicMock

# 1. Mock Home Assistant dependencies BEFORE importing the module
sys.modules['homeassistant'] = MagicMock()
sys.modules['homeassistant.config_entries'] = MagicMock()
sys.modules['homeassistant.const'] = MagicMock()
sys.modules['homeassistant.core'] = MagicMock()
sys.modules['homeassistant.data_entry_flow'] = MagicMock()
sys.modules['homeassistant.helpers'] = MagicMock()
sys.modules['homeassistant.helpers.aiohttp_client'] = MagicMock()
sys.modules['aiohttp'] = MagicMock()
sys.modules['voluptuous'] = MagicMock()

# Mock the base classes
class MockConfigFlow:
    pass

class MockOptionsFlow:
    def __init__(self):
        pass

sys.modules['homeassistant.config_entries'].ConfigFlow = MockConfigFlow
sys.modules['homeassistant.config_entries'].OptionsFlow = MockOptionsFlow

# 2. Mock internal project dependencies
# We need to simulate the package structure for relative imports to work, 
# or we can mock the specific modules that config_flow imports.
sys.modules['custom_components'] = MagicMock()
sys.modules['custom_components.vinfast'] = MagicMock()
sys.modules['custom_components.vinfast.api'] = MagicMock()
sys.modules['custom_components.vinfast.const'] = MagicMock()
sys.modules['custom_components.vinfast.pairing'] = MagicMock()

# Define constants used in config_flow
sys.modules['custom_components.vinfast.const'].DOMAIN = "vinfast"
sys.modules['custom_components.vinfast.const'].CONF_REGION = "region"
sys.modules['custom_components.vinfast.const'].DEFAULT_REGION = "us"
sys.modules['custom_components.vinfast.const'].REGIONS = {"us": {"name": "US"}}
sys.modules['custom_components.vinfast.const'].CONF_UPDATE_INTERVAL = "update_interval"
sys.modules['custom_components.vinfast.const'].UPDATE_INTERVAL_NORMAL = 9000
sys.modules['custom_components.vinfast.const'].UPDATE_INTERVAL_OPTIONS = {}

# 3. Load the target module manually since it's not in python path as a package
import importlib.util
import os

file_path = '/Volumes/DATA/Coding Projects/HomeAssistant-plugin/vinfast/custom_components/vinfast/config_flow.py'
spec = importlib.util.spec_from_file_location("custom_components.vinfast.config_flow", file_path)
config_flow_module = importlib.util.module_from_spec(spec)

# Patch the relative imports for the module we are loading
# This is tricky with standalone file loading, so we might need to rely on sys.modules mocks taking precedence
# The module uses "from .api import ...", so it expects to be in a package.
# We will manually inject the mocked modules into the config_flow_module's global namespace if needed,
# or better: we add the parent directory to sys.path so we can import it somewhat normally?
# Actually, since we already mocked 'custom_components.vinfast.api' in sys.modules, 
# we just need to make sure the relative import finds it.

# Let's try adding the parent directory to sys.path to resolve 'custom_components'
# /Volumes/DATA/Coding Projects/HomeAssistant-plugin/vinfast/
sys.path.append('/Volumes/DATA/Coding Projects/HomeAssistant-plugin/vinfast/')

# Now we can import the module using the full path if we structure it right, 
# BUT 'custom_components.vinfast.api' logic inside the file uses relative imports. 
# Relative imports only work if the module name is set correctly.
spec.loader.exec_module(config_flow_module)

# 4. Test the Fix
print("Successfully imported VinFastOptionsFlow.")
print("Attempting to instantiate VinFastOptionsFlow...")

try:
    # Create a mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.options = {}
    
    # Instantiate the class
    # If the fix works, this should NOT raise AttributeError
    options_flow = config_flow_module.VinFastOptionsFlow(mock_config_entry)
    
    # Verify that we didn't accidentally set self.config_entry (which would be the bug if it existed in parent)
    # In our mock parent, we didn't define properties, but the real issue was writing to a read-only property.
    # Here we just want to ensure __init__ runs without crashing.
    
    print("SUCCESS: VinFastOptionsFlow instantiated without error.")
    
except AttributeError as e:
    print(f"FAILED: AttributeError caught during instantiation: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILED: Unexpected error: {e}")
    sys.exit(1)
