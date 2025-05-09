#!/usr/bin/env python3
# post_single_tweet.py

import logging
import sys
sys.path.append('.')

from api_client import initialize_xai_client, initialize_x_client, post_tweet
from content_generator import select_content_type, generate_post

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Post a single tweet for testing purposes."""
    logger.info("Starting single tweet posting process")
    
    try:
        # Get xAI headers for content generation
        xai_headers = initialize_xai_client()
        if not xai_headers:
            logger.error("Failed to get xAI API headers")
            return
        
        # Initialize X API client
        x_client = initialize_x_client()
        if not x_client:
            logger.error("Failed to initialize X API client")
            return
        
        # Select content type
        content_type, theme = select_content_type()
        logger.info(f"Selected content type: {content_type}")
        
        # Generate post content
        content = generate_post(xai_headers, content_type, theme)
        if not content:
            logger.error("Failed to generate content")
            return
        
        logger.info(f"Generated content: {content}")
        
        # Post the tweet
        tweet_id = post_tweet(x_client, content)
        if tweet_id:
            logger.info(f"Successfully posted tweet with ID: {tweet_id}")
        else:
            logger.error("Failed to post tweet")
    except Exception as e:
        logger.error(f"Error in posting single tweet: {e}")

if __name__ == "__main__":
    main() 