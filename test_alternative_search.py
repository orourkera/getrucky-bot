#!/usr/bin/env python
# test_alternative_search.py - Test different search approaches and parameters

import logging
import sys
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
        # Import dependencies
        import api_client
        import tweepy
        from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, X_BEARER_TOKEN
        
        # Setup the X client
        logger.info("Initializing X client...")
        x_client = api_client.initialize_x_client(verify=True)
        
        # Try different search terms with various strategies
        test_terms = [
            "rucking",
            "ruck",
            "hiking",
            "goruck",
            "fitness hiking",
            "rucking workout",
            "ruck training",
            "hiking workout",
            "#rucking",
            "#hiking",
            "goruck challenge"
        ]
        
        # Add language filter and expand result count
        for query in test_terms:
            logger.info(f"Testing alternative search: '{query}'")
            try:
                # Try with expanded parameters and no minimum likes
                logger.info(f"Searching for '{query}' with expanded parameters")
                response = x_client.search_recent_tweets(
                    query=query, 
                    max_results=100,
                    tweet_fields=['public_metrics', 'created_at', 'author_id', 'lang'],
                    expansions=['author_id'],
                    user_fields=['username', 'public_metrics'],
                )
                
                if response.data:
                    logger.info(f"Found {len(response.data)} tweets for '{query}'")
                    
                    # Check how many tweets are in English
                    english_tweets = [t for t in response.data if getattr(t, 'lang', '') == 'en']
                    logger.info(f"  - English tweets: {len(english_tweets)}/{len(response.data)}")
                    
                    # Check how many have at least 1 like
                    liked_tweets = [t for t in response.data 
                                   if hasattr(t, 'public_metrics') 
                                   and t.public_metrics.get('like_count', 0) >= 1]
                    logger.info(f"  - Tweets with ≥1 like: {len(liked_tweets)}/{len(response.data)}")
                    
                    # Check popular tweets (10+ likes)
                    popular_tweets = [t for t in response.data 
                                     if hasattr(t, 'public_metrics') 
                                     and t.public_metrics.get('like_count', 0) >= 10]
                    logger.info(f"  - Popular tweets (≥10 likes): {len(popular_tweets)}/{len(response.data)}")
                    
                    # Get a sample tweet
                    if response.data:
                        sample = response.data[0]
                        author_id = sample.author_id
                        author = next((u for u in response.includes['users'] if u.id == author_id), None)
                        
                        logger.info(f"Sample tweet: {sample.text[:100]}...")
                        if author:
                            logger.info(f"  - Author: @{author.username} ({author.public_metrics.get('followers_count', 0)} followers)")
                        logger.info(f"  - Created: {sample.created_at}")
                        logger.info(f"  - Metrics: {sample.public_metrics}")
                else:
                    logger.warning(f"No tweets found for '{query}'")
                    
                # Sleep briefly to avoid rate limits
                time.sleep(2)
                
            except tweepy.errors.TooManyRequests as e:
                # Extract the reset time from the error
                reset_time = getattr(e, 'retry_after', 60)
                logger.warning(f"Rate limit hit while testing '{query}'. Reset in {reset_time} seconds.")
                if reset_time < 30:  # Only wait if it's a short time
                    time.sleep(reset_time + 1)
                continue
            except Exception as e:
                logger.error(f"Error testing search term '{query}': {e}")
                continue
                
        logger.info("Alternative search testing complete")
    except Exception as e:
        logger.error(f"Error in test script: {e}", exc_info=True)

if __name__ == "__main__":
    main() 