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
import tweepy

logger = logging.getLogger(__name__)

# Database path
INTERACTION_LOG_DB = '/tmp/interaction_log.db'


def monitor_mentions(x_client, xai_headers):
    """Monitor mentions of @getrucky and reply based on enhanced sentiment analysis."""
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
            
            # Search for mentions with specific error handling
            try:
                me = x_client.get_me() # Necessary to get the ID for mentions endpoint
                if not me.data:
                    logger.error("Could not get user ID for mention monitoring.")
                    time.sleep(300)
                    continue

                mentions_response = x_client.get_users_mentions(me.data.id, since_id=last_id, max_results=20)
                mentions = mentions_response.data if mentions_response and mentions_response.data else []
            
            except tweepy.TooManyRequests:
                logger.warning("Rate limit hit on get_users_mentions. Sleeping for 15 minutes.")
                time.sleep(900) # Sleep for 15 minutes
                continue
            except tweepy.TweepyException as e_tweepy:
                logger.error(f"Error fetching mentions (TweepyException): {e_tweepy}")
                if e_tweepy.response is not None:
                    logger.error(f"API Response: {e_tweepy.response.status_code} - {e_tweepy.response.text}")
                time.sleep(300)
                continue

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
                sentiment, sentiment_context = analyze_sentiment(tweet_text)
                content_type = select_reply_content_type(sentiment, sentiment_context)
                mention_timestamp = mention.created_at.isoformat() if hasattr(mention, 'created_at') else datetime.utcnow().isoformat()
                
                # Generate context-aware reply
                reply_text = content_generator.generate_reply(
                    xai_headers,
                    tweet_text,
                    sentiment,
                    content_type,
                    sentiment_context
                )
                
                if len(reply_text) > 280:
                    reply_text = reply_text[:277] + '...'
                
                # Prefix with username to reply directly
                reply_text = f"@{username} {reply_text}"
                if len(reply_text) > 280:
                    reply_text = reply_text[:277] + '...'
                
                if api_client.reply_to_tweet(x_client, tweet_id, reply_text):
                    replies_count += 1
                    log_interaction(
                        tweet_id,
                        reply_text,
                        sentiment,
                        content_type,
                        mention_timestamp,
                        sentiment_context
                    )
                    logger.info(f"Replied to mention by @{username} with sentiment {sentiment}: {reply_text[:50]}...")
                
                # Small delay to avoid rate limiting
                time.sleep(10)
            
            logger.info(f"Processed {len(mentions)} mentions. Sleeping for 5 minutes.")
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Error monitoring mentions: {e}")
            time.sleep(600)  # Wait longer on error (10 minutes)

def analyze_sentiment(text):
    """Analyze the sentiment of the tweet text using TextBlob with enhanced context."""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Enhanced sentiment analysis with context
        sentiment_context = {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'is_question': '?' in text,
            'has_hashtags': '#' in text,
            'has_mentions': '@' in text,
            'length': len(text),
            'contains_ruck': 'ruck' in text.lower(),
            'contains_emojis': any(c in text for c in ['😀', '😊', '😍', '😢', '😡', '😤'])
        }
        
        # Determine sentiment with more granularity
        if polarity > 0.3:
            sentiment = 'very_positive'
        elif polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.3:
            sentiment = 'very_negative'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Adjust sentiment based on context
        if sentiment_context['is_question']:
            sentiment = f'question_{sentiment}'
        if sentiment_context['contains_ruck']:
            sentiment = f'ruck_{sentiment}'
        
        return sentiment, sentiment_context
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return 'neutral', {}

def select_reply_content_type(sentiment, sentiment_context):
    """Select a content type for the reply based on sentiment and context."""
    # Adjust weights based on sentiment and context
    adjusted_weights = CONTENT_WEIGHTS.copy()
    
    if sentiment.startswith('very_positive'):
        adjusted_weights['challenge'] *= 1.5  # Encourage challenges for positive users
        adjusted_weights['shoutout'] *= 1.3
    elif sentiment.startswith('very_negative'):
        adjusted_weights['meme'] *= 1.5  # Lighten mood with memes
        adjusted_weights['pun'] *= 1.3
    elif sentiment.startswith('question'):
        adjusted_weights['theme'] *= 1.5  # Provide informative content
        adjusted_weights['challenge'] *= 1.2
    elif sentiment.startswith('ruck'):
        adjusted_weights['shoutout'] *= 1.4  # Acknowledge rucking mentions
        adjusted_weights['challenge'] *= 1.2
    
    # Select content type based on adjusted weights
    rand = random.random()
    cumulative_weight = 0
    total_weight = sum(adjusted_weights.values())
    
    for content_type, weight in adjusted_weights.items():
        cumulative_weight += weight / total_weight
        if rand <= cumulative_weight:
            return content_type
    
    return 'pun'  # Default fallback

def log_interaction(tweet_id, reply_text, sentiment, content_type, mention_timestamp=None, sentiment_context=None):
    """Log interaction details to interaction_log.db with enhanced context."""
    try:
        conn = sqlite3.connect(INTERACTION_LOG_DB)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist with new columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                tweet_id TEXT PRIMARY KEY,
                reply_text TEXT,
                sentiment TEXT,
                content_type TEXT,
                timestamp TEXT,
                mention_timestamp TEXT,
                polarity REAL,
                subjectivity REAL,
                is_question INTEGER,
                has_hashtags INTEGER,
                has_mentions INTEGER,
                length INTEGER,
                contains_ruck INTEGER,
                contains_emojis INTEGER
            )
        """)
        
        # Insert interaction with context
        cursor.execute("""
            INSERT OR REPLACE INTO logs (
                tweet_id, reply_text, sentiment, content_type, timestamp, mention_timestamp,
                polarity, subjectivity, is_question, has_hashtags, has_mentions,
                length, contains_ruck, contains_emojis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(tweet_id),
            reply_text,
            sentiment,
            content_type,
            datetime.utcnow(),
            mention_timestamp,
            sentiment_context.get('polarity', 0),
            sentiment_context.get('subjectivity', 0),
            1 if sentiment_context.get('is_question', False) else 0,
            1 if sentiment_context.get('has_hashtags', False) else 0,
            1 if sentiment_context.get('has_mentions', False) else 0,
            sentiment_context.get('length', 0),
            1 if sentiment_context.get('contains_ruck', False) else 0,
            1 if sentiment_context.get('contains_emojis', False) else 0
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Logged interaction for tweet {tweet_id} with enhanced context")
        return True
    except Exception as e:
        logger.error(f"Error logging interaction for tweet {tweet_id}: {e}")
        return False 