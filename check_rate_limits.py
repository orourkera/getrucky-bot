#!/usr/bin/env python
# check_rate_limits.py

import logging
import sys
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    try:
        from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, X_BEARER_TOKEN
        import api_client
        
        # Check if credentials exist
        if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
            logger.error("Missing required Twitter API credentials")
            return

        # Initialize Twitter client
        logger.info("Initializing Twitter client...")
        x_client = api_client.initialize_x_client(verify=True)
        
        # Check rate limit status
        logger.info("Checking current rate limits...")
        resources = api_client.check_rate_limit_status()
        
        if resources:
            # Check specific endpoints we care about
            search_limits = resources.get('search', {}).get('/search/tweets', {})
            if search_limits:
                reset_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                         time.gmtime(search_limits.get('reset', 0)))
                logger.info(f"Search API: {search_limits.get('remaining', 'N/A')}/{search_limits.get('limit', 'N/A')} remaining, resets at {reset_time} UTC")
            
            # Test search to see actual rate limit info in headers
            logger.info("Testing search API with a sample query...")
            tweets = api_client.search_tweets(x_client, "ruck", min_likes=1)
            logger.info(f"Found {len(tweets)} tweets in sample search")
            
        logger.info("Rate limit check complete")
    except Exception as e:
        logger.error(f"Error checking rate limits: {e}", exc_info=True)

if __name__ == "__main__":
    main() 