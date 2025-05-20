#!/usr/bin/env python
# debug_search.py - Debug search functionality with detailed output

import logging
import sys
import random
import json

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
        import api_client
        import tweepy
        from config import SEARCH_TERMS, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
        
        # Setup the X client
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(verify=True)
        
        # Test each search term individually
        for query in SEARCH_TERMS:
            logger.info(f"Testing search term: '{query}'")
            try:
                # Try with no minimum likes filter first
                logger.info(f"Searching for '{query}' with NO minimum likes filter")
                # We'll use the direct client to get more details
                response = x_client.search_recent_tweets(
                    query=query, 
                    max_results=10,
                    tweet_fields=['public_metrics', 'created_at', 'author_id']
                )
                
                if not response.data:
                    logger.warning(f"No tweets found for '{query}'")
                    continue
                    
                logger.info(f"Found {len(response.data)} tweets for '{query}'")
                
                # Print the first tweet details for debugging
                tweet = response.data[0]
                author = x_client.get_user(id=tweet.author_id).data
                logger.info(f"Sample tweet: {tweet.text[:50]}...")
                logger.info(f"  - Author: @{author.username}")
                logger.info(f"  - Created: {tweet.created_at}")
                logger.info(f"  - Metrics: {tweet.public_metrics}")
                
                # Now check how many would pass the minimum likes filter
                min_likes = 1
                filtered_tweets = [t for t in response.data 
                                  if hasattr(t, 'public_metrics') 
                                  and t.public_metrics.get('like_count', 0) >= min_likes]
                logger.info(f"After filtering for min {min_likes} likes: {len(filtered_tweets)} tweets remain")
                
            except tweepy.errors.TooManyRequests:
                logger.warning(f"Rate limit hit while testing '{query}'. Moving to next term.")
                continue
            except Exception as e:
                logger.error(f"Error testing search term '{query}': {e}")
                continue
                
        logger.info("Search debugging complete")
    except Exception as e:
        logger.error(f"Error in debug script: {e}", exc_info=True)

if __name__ == "__main__":
    main() 