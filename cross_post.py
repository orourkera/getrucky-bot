# cross_post.py

import random
import logging
import sqlite3
from datetime import datetime
import api_client
import content_generator
from config import SEARCH_TERMS, LIKE_PROBABILITY, RETWEET_ACCOUNTS, MIN_FOLLOWERS

logger = logging.getLogger(__name__)

# Database path
ANALYTICS_DB = '/tmp/analytics.db'


def engage_with_posts(x_client, xai_headers):
    """Engage with posts by liking, retweeting, and commenting."""
    try:
        query = random.choice(SEARCH_TERMS)
        tweets = api_client.search_tweets(x_client, query)
        engagement_count = {'liked': 0, 'retweeted': 0, 'commented': 0}
        
        for tweet in tweets:
            tweet_id = tweet.id
            username = tweet.user.screen_name
            
            # Like with 90% probability
            if random.random() < LIKE_PROBABILITY:
                if api_client.like_tweet(x_client, tweet_id):
                    engagement_count['liked'] += 1
                    log_engagement(tweet_id, 'like')
            
            # Check retweet eligibility
            followers = api_client.get_user_followers(x_client, username)
            if username in RETWEET_ACCOUNTS or followers > MIN_FOLLOWERS:
                if api_client.retweet(x_client, tweet_id):
                    engagement_count['retweeted'] += 1
                    log_engagement(tweet_id, 'retweet')
            
            # Cross-posting comment (limit to 10 per week - rough control via random sampling)
            if random.random() < 0.1:  # Rough approximation to limit cross-posts to about 10/week
                prompt = "Generate a comment for a rucking post, promoting @getrucky, <280 characters."
                comment_text = content_generator.get_cached_response(prompt)
                if not comment_text:
                    comment_text = api_client.generate_text(xai_headers, prompt)
                    content_generator.cache_response(prompt, comment_text)
                if comment_text and len(comment_text) <= 280:
                    if api_client.reply_to_tweet(x_client, tweet_id, comment_text):
                        engagement_count['commented'] += 1
                        log_engagement(tweet_id, 'comment')
        
        logger.info(f"Engagement results for query '{query}': Liked {engagement_count['liked']}, Retweeted {engagement_count['retweeted']}, Commented {engagement_count['commented']}")
        return engagement_count
    except Exception as e:
        logger.error(f"Error during engagement with posts: {e}")
        return {'liked': 0, 'retweeted': 0, 'commented': 0}

def log_engagement(tweet_id, action):
    """Log engagement actions to analytics.db."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO engagement (tweet_id, action, timestamp)
            VALUES (?, ?, ?)
        """, (str(tweet_id), action, datetime.utcnow()))
        conn.commit()
        conn.close()
        logger.info(f"Logged {action} for tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error logging {action} for tweet {tweet_id}: {e}")
        return False 