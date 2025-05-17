# content_generator.py

import random
import logging
import sqlite3
import os
from datetime import datetime
import api_client
from config import CONTENT_WEIGHTS, WEEKLY_THEMES, POST_FREQUENCY
import config

logger = logging.getLogger(__name__)

# Database paths
PUN_LIBRARY_DB = '/tmp/pun_library.db'
MODEL_CACHE_DB = '/tmp/model_cache.db'


def select_content_type():
    """Select content type based on weighted probability or weekly theme."""
    current_day = datetime.utcnow().weekday()
    
    # On specified map post days, increase chance of map posts
    if current_day in getattr(config, 'MAP_POST_DAYS', [1, 4]):  # Tuesdays and Fridays by default
        if random.random() < 0.3:  # 30% chance for map post on these days
            return 'map_post', None
    
    if random.random() < 0.2:  # 20% chance to use weekly theme for health benefits posts
        return 'health_benefits', WEEKLY_THEMES[current_day]
    else:
        rand = random.random()
        cumulative_weight = 0
        for content_type, weight in CONTENT_WEIGHTS.items():
            cumulative_weight += weight
            if rand <= cumulative_weight:
                return content_type, None
        return 'pun', None  # Default fallback

def generate_post(xai_headers, content_type, theme=None):
    """Generate a post based on the specified content type."""
    # Special case for map posts - we don't use the xAI API for these
    if content_type == 'map_post':
        from supabase_client import initialize_supabase_client, get_session_with_map
        try:
            supabase_client = initialize_supabase_client()
            session_data, map_path = get_session_with_map(supabase_client)
            if session_data and map_path:
                # We'll return the session data and map path, which will be handled by a separate function
                return {'session_data': session_data, 'map_path': map_path, 'is_map_post': True}
            else:
                logger.warning("Could not generate map post, falling back to health benefits")
                content_type = 'health_benefits'
        except Exception as e:
            logger.error(f"Error generating map post: {e}")
            content_type = 'health_benefits'
    
    # Standard content generation for non-map posts
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
    
    prompt = f"""Create a brief shout-out post for a ruck session:
    User: {user}
    Distance: {distance} miles
    Duration: {time}
    Achievements: {achievement_text if achievement_text else 'None'}
    Include 1-2 relevant emojis and ONE hashtag maximum. IMPORTANT: Keep response UNDER 200 characters total."""
    
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
    """Return the appropriate prompt for the content type with clear focus on specific topics."""
    current_month = datetime.utcnow().month
    season = get_season(current_month)

    base_prompts = {
        'pun': "You are a world class comedian, and goofy, slightly awkward marketing intern. Create a witty rucking pun that would make fellow ruckers smile, playing on things that rhyme with ruck and rucking, including profane ones like 'go ruck yourself'. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'challenge': f"Generate a {season}-themed rucking challenge that encourages community participation with specific goals and measurable targets. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'health_benefits': f"You are a goofy slightly awkward marketing intern and an avid outdoorsman, health scientist and researcher. You like data points and facts. Generate a {theme} post about the health and fitness benefits of rucking. Include ONE specific fact or statistic. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'poll': "You are a goofy slightly awkward marketing intern and an avid outdoorsman. Create an engaging poll about rucking preferences with specific options related to gear, training methods, or favorite locations. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'meme': "You are a goofy slightly awkward marketing intern and an avid outdoorsman. Create a relatable rucking meme about training struggles or gear preparations with a specific humorous scenario. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'shoutout': "You are a goofy slightly awkward marketing intern and an avid outdoorsmanGenerate a motivational shout-out for a rucking achievement with specific details about the accomplishment and encouraging words. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'ugc': "You are a goofy slightly inept awkward intern and an avid outdoorsman. Create a supportive comment for a user's rucking post with specific feedback about their achievement or effort. IMPORTANT: Keep response UNDER 200 characters total.",
        
        'map_post': "You are a goofy slightly awkward marketing intern and an avid outdoorsman. Generate a brief caption for a mapped ruck session, highlighting distance, pace, and achievement. IMPORTANT: Keep response UNDER 200 characters total."
    }

    # Handle the renamed theme category
    if content_type == 'theme':
        content_type = 'health_benefits'
    
    prompt = base_prompts.get(content_type, base_prompts['pun'])
    return prompt

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

def generate_map_post_text(session_data):
    """Generate text for a map post based on session data."""
    # Extract data for the tweet
    distance = session_data.get('distance', '0')
    duration = session_data.get('duration', '0h')
    pace = session_data.get('pace', 'N/A')
    weight = session_data.get('ruck_weight', '0')
    elevation = session_data.get('elevation_gain', '0')
    
    # Get location data from session - don't use defaults
    city = session_data.get('city', '')
    state = session_data.get('state', '')
    country = session_data.get('country', '')
    
    location_text = ""
    if city and state and country:
        location_text = f"Ruck of the day from {city}, {state}, {country}. "
    elif city and country:
        location_text = f"Ruck of the day from {city}, {country}. "
    elif city:
        location_text = f"Ruck of the day from {city}. "
    else:
        location_text = "Ruck of the day. "
    
    # Try to use XAI to generate an insightful observation about the ruck
    # Only do this if we're not in a testing environment
    if 'XAI_API_KEY' in os.environ:
        try:
            # Format the session data for the prompt
            session_details = f"""
            Distance: {distance} miles
            Duration: {duration}
            Pace: {pace}/mile
            Weight: {weight}kg
            Elevation gain: {elevation}m
            Location: {city}, {state}, {country}
            """
            
            # Create the prompt for observation
            prompt = f"""You are a rucking enthusiast and coach analyzing a ruck session. 
            Make ONE keen, specific observation about this ruck (less than 100 characters):
            {session_details}
            
            Focus on something impressive, unusual, or notable about this specific session.
            KEEP YOUR OBSERVATION VERY BRIEF."""
            
            # Initialize xAI client
            xai_headers = api_client.initialize_xai_client()
            
            # Generate the observation
            observation = api_client.generate_text(xai_headers, prompt)
            
            # Limit the length just to be safe
            if observation and len(observation) > 100:
                observation = observation[:97] + "..."
                
            logger.info(f"Generated XAI observation: {observation}")
            
            # Use the observation in our post
            if observation:
                # Create the tweet text with the observation
                post_text = f"{location_text}{observation}"
            else:
                # Fall back to standard format without observation
                post_text = f"{location_text}Great job rucker!"
                
        except Exception as e:
            logger.error(f"Error generating XAI observation: {e}")
            # Fall back to standard format without observation
            post_text = f"{location_text}Great job rucker!"
    else:
        # Standard format without XAI
        post_text = f"{location_text}Great job rucker!"
    
    # Format stats for readability with emojis
    stats_parts = []
    
    # Distance with running emoji
    if distance and float(distance) > 0:
        stats_parts.append(f"🏃‍♂️ {distance} miles")
    
    # Duration with clock emoji
    if duration and duration != "0h" and duration != "N/A":
        stats_parts.append(f"⏱️ {duration}")
    
    # Weight with backpack emoji
    if weight and float(weight) > 0:
        stats_parts.append(f"🎒 {weight}kg")
    
    # Pace with lightning emoji if available
    if pace and pace != "N/A":
        stats_parts.append(f"⚡ {pace}/mi")
    
    # Elevation with mountain emoji if available and significant
    if elevation and float(elevation) > 10:
        stats_parts.append(f"⛰️ {elevation}m gain")
    
    # Join the stats parts with commas for readability
    stats = ", ".join(stats_parts)
    
    # Combine the required format with the stats
    combined_text = f"{post_text} {stats}"
    
    # Make sure it's under the character limit
    max_length = 200  # Leave room for timestamps and any additional text
    if len(combined_text) > max_length:
        # If we need to truncate, keep the required format intact
        # and truncate the stats portion
        extra_chars = len(combined_text) - max_length
        if len(stats) > extra_chars + 3:  # +3 for ellipsis
            shortened_stats = stats[:-extra_chars-3] + "..."
            combined_text = f"{post_text} {shortened_stats}"
        else:
            # If stats are too short to meaningfully truncate, just use the main format
            combined_text = post_text
    
    return combined_text 