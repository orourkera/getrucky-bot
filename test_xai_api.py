#!/usr/bin/env python
# test_xai_api.py - Production test for XAI API on Heroku

import os
import logging
import traceback
import random
import api_client
import content_generator
from config import CONTENT_WEIGHTS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run a full production test with XAI API on Heroku."""
    try:
        # Initialize API clients
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(max_retries=3, retry_delay=5, verify=False)
        logger.info("Initializing XAI client...")
        xai_headers = api_client.initialize_xai_client()
        
        # Randomly select a content type based on distribution weights
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
        
        # Generate content using XAI
        logger.info(f"Generating content with type: {selected_content_type}")
        post_text = content_generator.generate_post(xai_headers, selected_content_type)
        
        # Ensure it's within character limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        # Post tweet
        logger.info(f"Posting tweet: {post_text}")
        logger.info(f"Tweet length: {len(post_text)} characters")
        tweet_id = api_client.post_tweet(x_client, post_text)
        
        if tweet_id:
            logger.info(f"Successfully posted tweet with ID: {tweet_id}")
            return True
        else:
            logger.error("Failed to get tweet ID - posting likely failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during XAI API test: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"XAI API test {'succeeded' if success else 'failed'}") 