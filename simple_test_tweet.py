#!/usr/bin/env python3
# simple_test_tweet.py - Minimal test of tweet posting

import logging
import api_client
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Post a single test tweet with minimal setup."""
    # Use a very simple fixed message to avoid API calls to generate content
    test_message = "This is a simple test tweet from @getrucky bot! 🥾 #GetRucky #TestTweet"
    
    try:
        # Initialize X client directly without verification (trust config)
        logger.info("Initializing X client without verification")
        x_client = api_client.tweepy.Client(
            bearer_token=api_client.X_BEARER_TOKEN,
            consumer_key=api_client.X_API_KEY,
            consumer_secret=api_client.X_API_SECRET,
            access_token=api_client.X_ACCESS_TOKEN,
            access_token_secret=api_client.X_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        logger.info("Successfully initialized X client")
        
        # Post the test tweet
        logger.info(f"Posting test tweet: {test_message}")
        result = x_client.create_tweet(text=test_message)
        
        # Check if tweet was successful
        if result and hasattr(result, 'data') and 'id' in result.data:
            tweet_id = result.data['id']
            logger.info(f"Successfully posted test tweet with ID: {tweet_id}")
            logger.info(f"View at: https://twitter.com/getrucky/status/{tweet_id}")
            return True
        else:
            logger.error("Failed to post tweet - no tweet ID returned")
            return False
            
    except Exception as e:
        logger.error(f"Error posting test tweet: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                logger.error(f"Response: {e.response.status_code} - {e.response.text}")
            except:
                pass
        return False

if __name__ == "__main__":
    main() 