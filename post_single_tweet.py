import os
import logging
import tweepy
import sys
sys.path.append('.')
from config import get_config
from api_client import post_tweet
from content_generator import select_content_type, generate_post

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Generate and post a single tweet for testing."""
    logger.info("Starting single tweet post test...")
    
    # Select content type based on weights
    content_type_data = select_content_type()
    # Handle if select_content_type returns a tuple or single value
    if isinstance(content_type_data, tuple):
        content_type = content_type_data[0]  # Take the first element if it's a tuple
    else:
        content_type = content_type_data
    logger.info(f"Selected content type: {content_type}")
    
    # Generate post content
    post_content = generate_post(content_type)
    logger.info(f"Generated post content: {post_content}")
    
    # Post the tweet
    try:
        tweet_id = post_tweet(post_content)
        logger.info(f"Successfully posted tweet with ID: {tweet_id}")
    except Exception as e:
        logger.error(f"Failed to post tweet: {str(e)}")

if __name__ == '__main__':
    main() 