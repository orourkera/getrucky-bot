# interaction_handler.py

import time
import logging
import sqlite3
from datetime import datetime
import random
from textblob import TextBlob
import api_client
import content_generator
from config import MAX_REPLIES, CONTENT_WEIGHTS

logger = logging.getLogger(__name__)

# Database path
INTERACTION_LOG_DB = '/tmp/interaction_log.db'


def monitor_mentions(x_client, xai_headers):
    """Monitor mentions of @getrucky and reply based on sentiment."""
    last_id = None
    replies_count = 0
    start_time = time.time()
    
    logger.info("Starting to monitor mentions for @getrucky")
    while True:
        try:
            # Reset reply count every hour
            if time.time() - start_time > 3600:
                replies_count = 0
                start_time = time.time()
                logger.info("Reset reply count for new hour")
            
            if replies_count >= MAX_REPLIES:
                logger.warning(f"Reached max replies ({MAX_REPLIES}) for this hour. Pausing until next hour.")
                time.sleep(3600 - (time.time() - start_time))
                continue
            
            # Search for mentions
            mentions = x_client.get_mentions_timeline(since_id=last_id, count=20)
            if not mentions:
                logger.info("No new mentions found. Sleeping for 5 minutes.")
                time.sleep(300)  # Sleep for 5 minutes if no mentions
                continue
            
            for mention in reversed(mentions):
                tweet_id = mention.id
                if last_id is None or tweet_id > last_id:
                    last_id = tweet_id
                
                tweet_text = mention.text
                username = mention.user.screen_name
                sentiment = analyze_sentiment(tweet_text)
                content_type = select_reply_content_type()
                
                reply_text = content_generator.generate_reply(xai_headers, tweet_text, sentiment, content_type)
                if len(reply_text) > 280:
                    reply_text = reply_text[:277] + '...'
                
                # Prefix with username to reply directly
                reply_text = f"@{username} {reply_text}"
                if len(reply_text) > 280:
                    reply_text = reply_text[:277] + '...'
                
                if api_client.reply_to_tweet(x_client, tweet_id, reply_text):
                    replies_count += 1
                    log_interaction(tweet_id, reply_text, sentiment, content_type)
                    logger.info(f"Replied to mention by @{username} with sentiment {sentiment}: {reply_text[:50]}...")
                
                # Small delay to avoid rate limiting
                time.sleep(10)
            
            logger.info(f"Processed {len(mentions)} mentions. Sleeping for 5 minutes.")
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Error monitoring mentions: {e}")
            time.sleep(600)  # Wait longer on error (10 minutes)

def analyze_sentiment(text):
    """Analyze the sentiment of the tweet text using TextBlob."""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return 'neutral'

def select_reply_content_type():
    """Select a content type for the reply based on weighted probability."""
    rand = random.random()
    cumulative_weight = 0
    for content_type, weight in CONTENT_WEIGHTS.items():
        cumulative_weight += weight
        if rand <= cumulative_weight:
            return content_type
    return 'pun'  # Default fallback

def log_interaction(tweet_id, reply_text, sentiment, content_type):
    """Log interaction details to interaction_log.db."""
    try:
        conn = sqlite3.connect(INTERACTION_LOG_DB)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO logs (tweet_id, reply_text, sentiment, content_type, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (str(tweet_id), reply_text, sentiment, content_type, datetime.utcnow()))
        conn.commit()
        conn.close()
        logger.info(f"Logged interaction for tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error logging interaction for tweet {tweet_id}: {e}")
        return False 