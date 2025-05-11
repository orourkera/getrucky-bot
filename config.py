# config.py

import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# API Credentials from Heroku environment variables
X_API_KEY = os.getenv('X_API_KEY', '')
X_API_SECRET = os.getenv('X_API_SECRET', '')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN', '')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET', '')
X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN', '')
APP_API_TOKEN = os.getenv('APP_API_TOKEN', '')
XAI_API_KEY = os.getenv('XAI_API_KEY', '')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', '')
SQLITE_DB_PATH = '/tmp'  # Heroku ephemeral filesystem

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_APP = os.getenv('FLASK_APP', 'dashboard.py')
PORT = int(os.getenv('PORT', '5000'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
PAPERTRAIL_API_TOKEN = os.getenv('PAPERTRAIL_API_TOKEN', '')

# Bot Configuration Constants
POST_FREQUENCY = range(5, 11)  # 5-10 posts per day
SEARCH_TERMS = ["ruck", "rucking", "#rucking", "#rucklife"]
MAX_REPLIES = 50  # Max replies per hour
POST_TIMES = [8, 10, 12, 15, 18, 21]  # UTC hours for posting
WEEKLY_THEMES = {
    0: "Motivation Monday",
    1: "Ruck Tips Tuesday",
    2: "Wellness Wednesday",
    3: "Throwback Thursday",
    4: "Fitness Friday",
    5: "Shout-out Saturday",
    6: "Ruck Fun Sunday"
}
CONTENT_WEIGHTS = {
    'pun': 0.3,
    'challenge': 0.2,
    'theme': 0.2,
    'poll': 0.1,
    'meme': 0.1,
    'shoutout': 0.05,
    'ugc': 0.05
}
LIKE_PROBABILITY = 0.9  # 90% chance to like 'ruck' posts
RETWEET_ACCOUNTS = ["GaryBrecka", "PeterAttiaMD"]
MIN_FOLLOWERS = 1000  # Minimum followers for retweet eligibility

# Content Moderation Blocklist
BLOCKLIST = ["inappropriate_word1", "inappropriate_word2"]  # Add more as needed

# Database paths
INTERACTION_LOG_DB = f"{SQLITE_DB_PATH}/interaction_log.db"
ANALYTICS_DB = f"{SQLITE_DB_PATH}/analytics.db"
MODEL_CACHE_DB = f"{SQLITE_DB_PATH}/model_cache.db"
PUN_LIBRARY_DB = f"{SQLITE_DB_PATH}/pun_library.db"

def get_config(key: str) -> Any:
    """Safely access environment variables or configuration values.
    
    Args:
        key: The configuration key to retrieve
        
    Returns:
        The configuration value or empty string if not found
        
    Raises:
        KeyError: If the key is not found and required=True
    """
    value = globals().get(key)
    if value is None:
        logger.warning(f"Configuration key '{key}' not found")
        return ''
    return value

def validate_config():
    required_keys = [
        'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET',
        'XAI_API_KEY'
    ]
    status = {}
    for key in required_keys:
        value = globals().get(key, '') or os.getenv(key, '')
        status[key] = bool(value)
    return status 