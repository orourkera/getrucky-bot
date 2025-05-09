# moderation.py

import time
import logging
import sqlite3
from datetime import datetime, timedelta
from config import BLOCKLIST

logger = logging.getLogger(__name__)

# Database path
ANALYTICS_DB = '/tmp/analytics.db'

# API rate limits
API_LIMITS = {
    'x_tweet': {'limit': 50, 'window_hours': 1},      # 50 tweets/hour
    'x_like': {'limit': 900, 'window_hours': 0.25},   # 900 likes/15min
    'x_retweet': {'limit': 300, 'window_hours': 3},   # 300 retweets/3h
    'x_search': {'limit': 450, 'window_hours': 0.25}, # 450 searches/15min
    'xai': {'limit': 100, 'window_hours': 1}          # Estimated xAI API limit
}


def filter_content(text):
    """Filter content for inappropriate words and flag for review if found."""
    if not text:
        return {'is_clean': True, 'flagged_words': []}
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check for blocked words
    flagged_words = []
    for word in BLOCKLIST:
        if word.lower() in text_lower:
            flagged_words.append(word)
    
    result = {
        'is_clean': len(flagged_words) == 0,
        'flagged_words': flagged_words
    }
    
    # Log if any words were flagged
    if not result['is_clean']:
        log_flagged_content(text, ', '.join(flagged_words))
        logger.warning(f"Content flagged for review. Flagged words: {', '.join(flagged_words)}")
    
    return result

def log_flagged_content(text, reason):
    """Log flagged content to analytics.db for manual review."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Ensure the flags table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                text TEXT,
                reason TEXT,
                timestamp TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO flags (text, reason, timestamp)
            VALUES (?, ?, ?)
        """, (text, reason, datetime.utcnow()))
        
        conn.commit()
        conn.close()
        logger.info(f"Logged flagged content to analytics.db: {reason}")
        return True
    except Exception as e:
        logger.error(f"Error logging flagged content: {e}")
        return False

def rate_limit_check(api_type):
    """
    Check if we're approaching rate limits for the specified API type.
    Returns a tuple (is_limited, wait_seconds).
    """
    if api_type not in API_LIMITS:
        logger.warning(f"Unknown API type for rate limit check: {api_type}")
        return False, 0
    
    limit_info = API_LIMITS[api_type]
    limit = limit_info['limit']
    window_hours = limit_info['window_hours']
    
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Get current time and calculate the window start time
        current_time = datetime.utcnow()
        window_start = (current_time - timedelta(hours=window_hours)).isoformat()
        
        # Count actions of this type within the window
        cursor.execute("""
            SELECT COUNT(*) FROM api_usage
            WHERE api_type = ? AND timestamp > ?
        """, (api_type, window_start))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        # Calculate usage percentage
        usage_percent = (count / limit) * 100
        
        # If we're over 80% of the limit, suggest waiting
        if usage_percent >= 80:
            # Calculate wait time - default to waiting until the window resets
            wait_seconds = int(window_hours * 3600)
            logger.warning(f"Rate limit for {api_type} at {usage_percent:.1f}% ({count}/{limit}). Suggesting wait of {wait_seconds} seconds.")
            return True, wait_seconds
        
        logger.info(f"Rate limit for {api_type} at {usage_percent:.1f}% ({count}/{limit}).")
        return False, 0
        
    except Exception as e:
        logger.error(f"Error checking rate limits for {api_type}: {e}")
        return True, int(window_hours * 3600)  # Be conservative on error

def log_api_call(api_type, endpoint=None, success=True):
    """Log an API call to track rate limit usage."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Ensure the api_usage table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                api_type TEXT,
                endpoint TEXT,
                success BOOLEAN,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO api_usage (api_type, endpoint, success, timestamp)
            VALUES (?, ?, ?, ?)
        """, (api_type, endpoint, success, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error logging API call: {e}")
        return False

def get_api_usage():
    """Get API usage statistics for the various APIs."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Get usage for last hour by API type
        hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        cursor.execute("""
            SELECT api_type, COUNT(*) FROM api_usage
            WHERE timestamp > ?
            GROUP BY api_type
        """, (hour_ago,))
        
        hourly_usage = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get usage for last day by API type
        day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        cursor.execute("""
            SELECT api_type, COUNT(*) FROM api_usage
            WHERE timestamp > ?
            GROUP BY api_type
        """, (day_ago,))
        
        daily_usage = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'hourly': hourly_usage,
            'daily': daily_usage,
            'limits': API_LIMITS
        }
        
    except Exception as e:
        logger.error(f"Error retrieving API usage: {e}")
        return {
            'hourly': {},
            'daily': {},
            'limits': API_LIMITS
        } 