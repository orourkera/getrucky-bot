#!/usr/bin/env python
# test_manual_post.py - Script to manually post a tweet

import logging
import api_client
import content_generator
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test posting a manual tweet."""
    try:
        # Initialize API client
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(max_retries=3, retry_delay=5, verify=False)
        logger.info("Initializing xAI client...")
        xai_headers = api_client.initialize_xai_client()
        
        # Generate content
        content_type = 'health_benefits'
        theme = "Test Manual Post"
        logger.info(f"Generating content with type: {content_type}, theme: {theme}")
        post_text = content_generator.generate_post(xai_headers, content_type, theme)
        
        # Add uniqueness
        current_time = datetime.utcnow().strftime('%H:%M:%S')
        post_text = f"Manual test [{current_time}]: {post_text}"
        
        # Ensure it's within character limit
        if len(post_text) > 280:
            post_text = post_text[:277] + '...'
        
        # Post tweet
        logger.info(f"Posting tweet: {post_text}")
        tweet_id = api_client.post_tweet(x_client, post_text)
        logger.info(f"Successfully posted tweet with ID: {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error during manual tweet test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Manual post test {'succeeded' if success else 'failed'}") 