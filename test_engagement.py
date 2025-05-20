#!/usr/bin/env python
# test_engagement.py - Test engagement functionality for Heroku deployment

import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    try:
        # Import dependencies
        import scheduler
        import api_client
        from config import OPENAI_API_KEY
        
        # Setup the X client
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(verify=True)
        
        # Setup AI headers
        logger.info("Initializing AI client...")
        ai_headers = api_client.initialize_ai_client()
        
        # Check search_tweets function with reduced threshold
        logger.info("Testing search functionality...")
        from config import SEARCH_TERMS
        import random
        
        # Randomly select a search term
        query = random.choice(SEARCH_TERMS)
        logger.info(f"Selected search term: {query}")
        
        # Search for tweets
        tweets = api_client.search_tweets(x_client, query, min_likes=1)
        logger.info(f"Found {len(tweets)} tweets matching '{query}' with at least 1 like")
        
        if len(tweets) > 0:
            # Show a sample tweet
            sample_tweet = tweets[0]
            logger.info(f"Sample tweet ID: {sample_tweet.id}")
            metrics = getattr(sample_tweet, 'public_metrics', {})
            logger.info(f"Metrics: {metrics}")
        
        # Run the engage_with_posts function
        logger.info("Testing engagement function...")
        result = scheduler.engage_with_posts(x_client, ai_headers)
        logger.info(f"Engagement results: {result}")
        
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Error running engagement test: {e}", exc_info=True)

if __name__ == "__main__":
    main() 