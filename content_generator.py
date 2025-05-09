# content_generator.py

import random
import logging
import sqlite3
from datetime import datetime
import api_client
from config import CONTENT_WEIGHTS, WEEKLY_THEMES, POST_FREQUENCY

logger = logging.getLogger(__name__)

# Database paths
PUN_LIBRARY_DB = '/tmp/pun_library.db'
MODEL_CACHE_DB = '/tmp/model_cache.db'


def select_content_type():
    """Select content type based on weighted probability or weekly theme."""
    current_day = datetime.utcnow().weekday()
    if random.random() < 0.2:  # 20% chance to use weekly theme based on CONTENT_WEIGHTS['theme']
        return 'theme', WEEKLY_THEMES[current_day]
    else:
        rand = random.random()
        cumulative_weight = 0
        for content_type, weight in CONTENT_WEIGHTS.items():
            if content_type != 'theme':
                cumulative_weight += weight
                if rand <= cumulative_weight:
                    return content_type, None
        return 'pun', None  # Default fallback

def generate_post(xai_headers, content_type, theme=None):
    """Generate a post based on the specified content type."""
    prompt = get_prompt_for_content_type(content_type, theme)
    cached_response = get_cached_response(prompt)
    if cached_response:
        logger.info(f"Using cached response for {content_type} post")
        return cached_response
    
    try:
        text = api_client.generate_text(xai_headers, prompt)
        if text:
            cache_response(prompt, text)
            logger.info(f"Generated {content_type} post with xAI API")
            return text
    except Exception as e:
        logger.error(f"Failed to generate {content_type} post with xAI API: {e}")
    
    # Fallback to template from pun_library.db
    return get_random_template('post', content_type)

def generate_session_post(xai_headers, session_data):
    """Generate a shout-out post for a ruck session."""
    user = session_data.get('user', 'RuckStar')
    distance = session_data.get('distance', '5')
    time = session_data.get('duration', '1h')
    prompt = f"Create a shout-out post for a ruck session: {user} rucked {distance} miles in {time}."
    cached_response = get_cached_response(prompt)
    if cached_response:
        logger.info(f"Using cached response for session post")
        return cached_response
    
    try:
        text = api_client.generate_text(xai_headers, prompt)
        if text:
            cache_response(prompt, text)
            logger.info(f"Generated session post with xAI API for {user}")
            return text
    except Exception as e:
        logger.error(f"Failed to generate session post with xAI API: {e}")
    
    # Fallback to template
    template = get_random_template('post', 'shoutout')
    return template.format(user=user, distance=distance)

def generate_reply(xai_headers, tweet_text, sentiment, content_type=None):
    """Generate a reply based on sentiment and optional content type."""
    if content_type:
        prompt = f"Generate a {sentiment} rucking {content_type} reply, <280 characters."
    else:
        prompt = f"Generate a {sentiment} rucking reply with a pun, <280 characters."
    cached_response = get_cached_response(prompt)
    if cached_response:
        logger.info(f"Using cached response for {sentiment} reply")
        return cached_response
    
    try:
        text = api_client.generate_text(xai_headers, prompt)
        if text:
            cache_response(prompt, text)
            logger.info(f"Generated {sentiment} reply with xAI API")
            return text
    except Exception as e:
        logger.error(f"Failed to generate {sentiment} reply with xAI API: {e}")
    
    # Fallback to template
    return get_random_template('reply', content_type if content_type else 'pun')

def get_prompt_for_content_type(content_type, theme=None):
    """Return the appropriate prompt for the content type."""
    prompts = {
        'pun': "Generate a rucking pun like 'Ruck it Up', <280 characters.",
        'challenge': "Generate a rucking challenge for 5 miles, <280 characters.",
        'theme': f"Generate a {theme} post (e.g., Ruck Tips Tuesday), <280 characters." if theme else "Generate a themed rucking post, <280 characters.",
        'poll': "Generate a rucking poll with 2-4 options, <280 characters.",
        'meme': "Generate a humorous rucking meme text, <280 characters.",
        'shoutout': "Generate a shout-out for @RuckStar rucking 5 miles, <280 characters.",
        'ugc': "Generate a comment for a user's ruck post by @RuckFan, <280 characters."
    }
    return prompts.get(content_type, prompts['pun'])

def get_random_template(post_type, category):
    """Fetch a random template from pun_library.db for the given type and category."""
    try:
        conn = sqlite3.connect(PUN_LIBRARY_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM templates WHERE type = ? AND category = ? ORDER BY RANDOM() LIMIT 1", (post_type, category))
        result = cursor.fetchone()
        conn.close()
        if result:
            logger.info(f"Fetched random {category} template for {post_type}")
            return result[0]
        else:
            logger.warning(f"No template found for {post_type}/{category}")
            return "Ruck it Up with @getrucky! 🥾 #GetRucky"
    except Exception as e:
        logger.error(f"Error fetching template from pun_library.db: {e}")
        return "Ruck it Up with @getrucky! 🥾 #GetRucky"

def insert_template(text, post_type, category):
    """Insert a new template into pun_library.db."""
    try:
        conn = sqlite3.connect(PUN_LIBRARY_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO templates (text, type, category) VALUES (?, ?, ?)", (text, post_type, category))
        conn.commit()
        conn.close()
        logger.info(f"Inserted new template for {post_type}/{category}")
        return True
    except Exception as e:
        logger.error(f"Error inserting template into pun_library.db: {e}")
        return False

def get_cached_response(prompt):
    """Retrieve a cached response for the given prompt from model_cache.db."""
    try:
        conn = sqlite3.connect(MODEL_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM cache WHERE prompt = ? AND timestamp > datetime('now', '-24 hours')", (prompt,))
        result = cursor.fetchone()
        conn.close()
        if result:
            logger.info(f"Retrieved cached response for prompt: {prompt[:30]}...")
            return result[0]
        return None
    except Exception as e:
        logger.error(f"Error retrieving cached response: {e}")
        return None

def cache_response(prompt, response):
    """Cache a generated response in model_cache.db with a timestamp."""
    try:
        conn = sqlite3.connect(MODEL_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO cache (prompt, response, timestamp) VALUES (?, ?, ?)", 
                       (prompt, response, datetime.utcnow()))
        conn.commit()
        conn.close()
        logger.info(f"Cached response for prompt: {prompt[:30]}...")
        return True
    except Exception as e:
        logger.error(f"Error caching response: {e}")
        return False 