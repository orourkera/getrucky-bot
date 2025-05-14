# tests/test_config.py

import os
import sys
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables for testing
TEST_ENV_VARS = {
    'X_API_KEY': 'test_x_api_key',
    'X_API_SECRET': 'test_x_api_secret',
    'X_ACCESS_TOKEN': 'test_x_access_token',
    'X_ACCESS_TOKEN_SECRET': 'test_x_access_token_secret',
    'X_BEARER_TOKEN': 'test_x_bearer_token',
    'XAI_API_KEY': 'test_xai_api_key',
    'APP_API_TOKEN': 'test_app_api_token',
    'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db'
}

def setup_test_env():
    """Set up test environment variables."""
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value

def teardown_test_env():
    """Clean up test environment variables."""
    for key in TEST_ENV_VARS:
        if key in os.environ:
            del os.environ[key]

def mock_get_config(key):
    """Mock get_config function for testing."""
    return TEST_ENV_VARS.get(key)

# Create a patch for get_config
patch_get_config = patch('config.get_config', side_effect=mock_get_config) 