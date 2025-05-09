# config.py

import os

# API Credentials from Heroku environment variables
X_API_KEY = os.getenv('X_API_KEY', '')
X_API_SECRET = os.getenv('X_API_SECRET', '')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN', '')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET', '')
APP_API_TOKEN = os.getenv('APP_API_TOKEN', '')
XAI_API_KEY = os.getenv('XAI_API_KEY', '')

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

def get_config(key):
    """Safely access environment variables or configuration values."""
    return globals().get(key, '') 