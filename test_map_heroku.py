#!/usr/bin/env python
# test_map_heroku.py - Script to test map generation on Heroku

import logging
import traceback
import api_client
import content_generator
from supabase_client import initialize_supabase_client, get_session_with_map

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test map generation and post on Heroku."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Initialize X client
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(max_retries=3, retry_delay=5, verify=False)
        
        # Fetch a session with map data
        logger.info("Fetching session data with map...")
        session_data, map_path = get_session_with_map(supabase_client)
        
        if not session_data:
            logger.error("No session data found")
            return False
            
        logger.info(f"Found session: {session_data.get('session_id')}")
        logger.info(f"Map path: {map_path}")
        
        # Debug location_point handling
        logger.info(f"Session city: {session_data.get('city', 'unknown')}")
        logger.info(f"Session state: {session_data.get('state', 'unknown')}")
        logger.info(f"Session country: {session_data.get('country', 'unknown')}")
        
        # Generate post text
        post_text = content_generator.generate_map_post_text(session_data)
        logger.info(f"Generated post text: {post_text}")
        
        # Only truncate if absolutely necessary for Twitter's character limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        # Post tweet
        logger.info(f"Posting tweet with text (length: {len(post_text)} chars):")
        logger.info(post_text)
        
        tweet_id = None
        if map_path:
            logger.info("Posting with map image...")
            tweet_id = api_client.post_tweet(x_client, post_text, media=map_path)
        else:
            logger.info("Posting without map image (not available)...")
            tweet_id = api_client.post_tweet(x_client, post_text)
        
        if tweet_id:
            logger.info(f"Successfully posted map tweet with ID: {tweet_id}")
            return True
        else:
            logger.error("Failed to post tweet")
            return False
    
    except Exception as e:
        logger.error(f"Error testing map post: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"Map post test {'succeeded' if success else 'failed'}") 