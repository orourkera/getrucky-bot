#!/usr/bin/env python3
# force_post.py - Test posting with full database setup

import logging
import sys
import os
import sqlite3
import api_client
import backup
import content_generator
from config import validate_config
from populate_templates import populate_templates

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Initialize databases, populate templates, and post a single tweet."""
    # Step 1: Validate configuration
    logger.info("Validating configuration")
    config_status = validate_config()
    # Check for essential keys only for script execution
    essential_keys_present = all([
        config_status.get('X_API_KEY', False),
        config_status.get('X_API_SECRET', False),
        config_status.get('X_ACCESS_TOKEN', False),
        config_status.get('X_ACCESS_TOKEN_SECRET', False),
        config_status.get('AI_API_KEY', False) # Checks if OPENAI_API_KEY is present
    ])

    if not essential_keys_present:
        logger.error("Missing essential (X API or AI API) environment variables. Please check the configuration. Exiting force_post.")
        sys.exit(1)
    
    if not config_status.get('MAP_KEYS', True):
        logger.warning("Map-related API keys (SUPABASE or STADIA) are missing. Map post functionality might be affected, but proceeding with force_post.")

    logger.info("Essential configuration validated successfully for force_post.")
    
    # Step 2: Initialize databases
    logger.info("Initializing databases")
    success = backup.initialize_databases()
    if not success:
        logger.warning("Database initialization had issues, will attempt to continue")
    
    # Step 3: Populate templates if needed
    pun_library_db = '/tmp/pun_library.db'
    try:
        conn = sqlite3.connect(pun_library_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM templates")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            logger.info("Template database is empty, populating with defaults")
            populate_templates()
        else:
            logger.info(f"Template database already contains {count} templates")
    except Exception as e:
        logger.error(f"Error checking templates: {e}")
        logger.info("Attempting to populate templates")
        populate_templates()
    
    # Step 4: Initialize API clients
    logger.info("Initializing API clients")
    try:
        # Make sure to verify credentials and use OAuth 1.0a explicitly
        logger.info("Initializing X client with OAuth 1.0a authentication")
        x_client = api_client.initialize_x_client(max_retries=5, retry_delay=10, verify=True)
        
        # Additional verification to ensure the client is using OAuth 1.0a
        if not hasattr(x_client, 'access_token') or not x_client.access_token:
            logger.warning("X client may not be properly configured with OAuth 1.0a")
            # Proceed anyway, but log the warning
        
        ai_client_headers = api_client.initialize_ai_client()
        logger.info("API clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        sys.exit(1)
    
    # Step 5: Post a test tweet
    logger.info("Posting a test tweet with full tracking")
    try:
        content_type, theme = content_generator.select_content_type()
        post_text = content_generator.generate_post(ai_client_headers, content_type, theme)
        
        logger.info(f"Generated post text for content type '{content_type}': {post_text[:50]}...")
        
        if len(post_text) > 280:
            post_text = post_text[:277] + '...'
        
        # Explicitly call post_tweet with proper OAuth 1.0a client    
        logger.info("Posting tweet using OAuth 1.0a authentication")
        tweet_id = api_client.post_tweet(x_client, post_text)
        
        if not tweet_id:
            logger.error("No tweet ID returned - posting likely failed")
            return False
        
        # Log the tweet to interaction_log.db
        try:
            conn = sqlite3.connect('/tmp/interaction_log.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO logs (tweet_id, content_type, timestamp) VALUES (?, ?, datetime('now'))",
                (tweet_id, content_type)
            )
            conn.commit()
            conn.close()
            logger.info(f"Logged tweet {tweet_id} to interaction_log.db")
        except Exception as log_error:
            logger.error(f"Error logging tweet to database: {log_error}")
        
        logger.info(f"Successfully posted and tracked test tweet: {post_text[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Error posting test tweet: {e}")
        return False

if __name__ == "__main__":
    main() 