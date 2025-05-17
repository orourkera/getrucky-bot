#!/usr/bin/env python
# post_single_tweet.py - Script to post a single tweet for testing

import logging
import api_client
import content_generator
import random
from config import CONTENT_WEIGHTS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Post a single tweet for testing."""
    try:
        # Initialize API client
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(max_retries=3, retry_delay=5, verify=False)
        logger.info("Initializing xAI client...")
        xai_headers = api_client.initialize_xai_client()
        
        # Randomly select content type based on weights
        rand = random.random()
        cumulative_weight = 0
        selected_content_type = None
        
        for content_type, weight in CONTENT_WEIGHTS.items():
            cumulative_weight += weight
            if rand <= cumulative_weight:
                selected_content_type = content_type
                break
        
        if not selected_content_type:
            selected_content_type = 'health_benefits'
        
        logger.info(f"Selected content type: {selected_content_type}")
        
        # Generate content
        post_text = content_generator.generate_post(xai_headers, selected_content_type)
        
        # Only truncate if absolutely necessary for Twitter's character limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        # Post tweet
        logger.info(f"Posting tweet: {post_text}")
        logger.info(f"Tweet length: {len(post_text)} characters")
        tweet_id = api_client.post_tweet(x_client, post_text)
        logger.info(f"Successfully posted tweet with ID: {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error posting single tweet: {e}")
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"Single tweet post {'succeeded' if success else 'failed'}") 