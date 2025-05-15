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
    if cached_response and len(cached_response) > 50:
        logger.info(f"Using cached response for {content_type} post")
        return cached_response

    try:
        text = api_client.generate_text(xai_headers, prompt)
        if text and len(text) > 50:
            cache_response(prompt, text)
            logger.info(f"Generated {content_type} post with xAI API")
            return text
    except Exception as e:
        logger.error(f"Failed to generate {content_type} post with xAI API: {e}")
        # Fall through to template-based backup

    # Fallback to template from pun_library.db
    template = get_random_template('post', content_type)
    logger.warning(f"Using template fallback for {content_type} post due to API failure")
    return template

def generate_session_post(xai_headers, session_data):
    """Generate a shout-out post for a ruck session with achievements and milestones."""
    user = session_data.get('user', 'RuckStar')
    distance = session_data.get('distance', '5')
    time = session_data.get('duration', '1h')
    total_distance = session_data.get('total_distance', '0')
    streak = session_data.get('streak', '0')
    
    # Check for achievements
    achievements = []
    if float(distance) >= 10:
        achievements.append("double-digit distance")
    if float(total_distance) >= 100:
        achievements.append("100-mile milestone")
    if int(streak) >= 7:
        achievements.append(f"{streak}-day streak")
    
    achievement_text = " and achieved " + ", ".join(achievements) if achievements else ""
    
    prompt = f"""Create an engaging shout-out post for a ruck session:
    User: {user}
    Distance: {distance} miles
    Duration: {time}
    Achievements: {achievement_text if achievement_text else 'None'}
    Include relevant emojis and hashtags. Keep it under 280 characters."""
    
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
    
    # Enhanced fallback template
    template = get_random_template('post', 'shoutout')
    logger.warning(f"Using template fallback for session post due to API failure")
    return template.format(
        user=user,
        distance=distance,
        achievements=achievement_text if achievement_text else "",
        emoji="🏆" if achievements else "🥾"
    )

def generate_reply(xai_headers, tweet_text, sentiment, content_type=None, sentiment_context=None):
    """Generate a reply based on sentiment, content type, and context."""
    # Build context-aware prompt
    prompt_parts = []
    
    # Add sentiment context
    if sentiment.startswith('very_positive'):
        prompt_parts.append("very enthusiastic and encouraging")
    elif sentiment.startswith('positive'):
        prompt_parts.append("positive and supportive")
    elif sentiment.startswith('very_negative'):
        prompt_parts.append("empathetic and uplifting")
    elif sentiment.startswith('negative'):
        prompt_parts.append("understanding and motivational")
    elif sentiment.startswith('question'):
        prompt_parts.append("informative and helpful")
    else:
        prompt_parts.append("friendly and engaging")
    
    # Add content type context
    if content_type:
        prompt_parts.append(f"rucking {content_type}")
    else:
        prompt_parts.append("rucking")
    
    # Add specific context elements
    if sentiment_context:
        if sentiment_context.get('contains_ruck'):
            prompt_parts.append("acknowledging their rucking mention")
        if sentiment_context.get('is_question'):
            prompt_parts.append("answering their question")
        if sentiment_context.get('contains_emojis'):
            prompt_parts.append("matching their tone")
    
    # Construct final prompt
    prompt = f"Generate a {' '.join(prompt_parts)} reply, <280 characters."
    
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
    
    # Enhanced fallback template selection based on sentiment
    template_category = 'positive' if sentiment.startswith(('very_positive', 'positive')) else \
                       'negative' if sentiment.startswith(('very_negative', 'negative')) else \
                       'question' if sentiment.startswith('question') else \
                       'neutral'
    
    template = get_random_template('reply', template_category)
    logger.warning(f"Using template fallback for {sentiment} reply due to API failure")
    return template

def get_prompt_for_content_type(content_type, theme=None):
    """Return the appropriate prompt for the content type with enhanced variety and minimum length."""
    current_month = datetime.utcnow().month
    season = get_season(current_month)

    base_prompts = {
        'pun': [
            "Generate a creative rucking pun that plays on words like 'ruck', 'pack', or 'march', <280 characters.",
            "Create a witty rucking pun that would make fellow ruckers smile, <280 characters.",
            "Write a clever rucking pun that incorporates fitness or outdoor themes, <280 characters."
        ],
        'challenge': [
            f"Generate a {season}-themed rucking challenge for 5 miles, <280 characters.",
            "Create a rucking challenge that encourages community participation, <280 characters.",
            "Design a progressive rucking challenge that builds endurance, <280 characters."
        ],
        'theme': [
            f"Generate a {theme} post about the health and fitness benefits of rucking. Make it informative and at least 50 characters, <280 characters.",
            f"Create an engaging {theme} post highlighting why rucking is good for you. Ensure it is at least 50 characters, <280 characters.",
            "List a science-backed benefit of rucking in a detailed way (at least 50 characters), <280 characters.",
            "Share a motivational fact about how rucking improves health. Minimum 50 characters, <280 characters."
        ],
        'poll': [
            "Generate a rucking poll about training preferences, <280 characters.",
            "Create a poll about favorite rucking locations, <280 characters.",
            "Design a poll about rucking gear preferences, <280 characters."
        ],
        'meme': [
            "Generate a humorous rucking meme about common rucking experiences, <280 characters.",
            "Create a relatable rucking meme about training struggles, <280 characters.",
            "Write a funny rucking meme about gear or preparation, <280 characters."
        ],
        'shoutout': [
            "Generate a motivational shout-out for a rucking achievement, <280 characters.",
            "Create an encouraging shout-out for consistent rucking, <280 characters.",
            "Write an inspiring shout-out for a rucking milestone, <280 characters."
        ],
        'ugc': [
            "Generate an engaging comment for a user's ruck post, <280 characters.",
            "Create a supportive comment for a rucking achievement, <280 characters.",
            "Write an encouraging comment for a rucking milestone, <280 characters."
        ]
    }

    prompts = base_prompts.get(content_type, base_prompts['pun'])
    return random.choice(prompts)

def get_season(month):
    """Return the current season based on month."""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"

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