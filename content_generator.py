# content_generator.py

import random
import logging
import sqlite3
import os
from datetime import datetime
import api_client
from config import CONTENT_WEIGHTS, WEEKLY_THEMES, POST_FREQUENCY, AI_PROVIDER, OPENAI_API_KEY
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

def generate_post(ai_headers, content_type, theme=None):
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
        text = api_client.generate_text(ai_headers, prompt)
        if text and len(text) > 50:
            cache_response(prompt, text)
            logger.info(f"Generated {content_type} post with {AI_PROVIDER} API")
            return text
    except Exception as e:
        logger.error(f"Failed to generate {content_type} post with {AI_PROVIDER} API: {e}")
        # Fall through to template-based backup

    # Fallback to template from pun_library.db
    template = get_random_template('post', content_type)
    logger.warning(f"Using template fallback for {content_type} post due to API failure")
    return template

def generate_session_post(ai_headers, session_data):
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
    
    prompt = f"""Create a brief, enthusiastic shout-out post for this ruck session:
User: {user}
Distance: {distance} miles
Duration: {time}
Achievements: {achievement_text if achievement_text else 'None'}

Keep the tone celebratory. Include 1-2 relevant emojis. Use a strong call to action or an inspiring message. 
End with ONE hashtag. IMPORTANT: Response strictly under 180 characters."""
    
    cached_response = get_cached_response(prompt)
    if cached_response:
        logger.info(f"Using cached response for session post")
        return cached_response
    
    try:
        text = api_client.generate_text(ai_headers, prompt)
        if text:
            cache_response(prompt, text)
            logger.info(f"Generated session post with {AI_PROVIDER} API for {user}")
            return text
    except Exception as e:
        logger.error(f"Failed to generate session post with {AI_PROVIDER} API: {e}")
    
    # Enhanced fallback template
    template = get_random_template('post', 'shoutout')
    logger.warning(f"Using template fallback for session post due to API failure")
    return template.format(
        user=user,
        distance=distance,
        achievements=achievement_text if achievement_text else "",
        emoji="🏆" if achievements else "🥾"
    )

def generate_reply(ai_headers, tweet_text, sentiment, content_type=None, sentiment_context=None):
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
    
    # Construct final user prompt for the reply generation task
    user_prompt = f"The user tweeted: '{tweet_text}'. My sentiment analysis is: '{sentiment}' with context: {sentiment_context}. Generate a reply that is {' '.join(prompt_parts)}. IMPORTANT: Response strictly under 240 characters."
    
    cached_response = get_cached_response(user_prompt)
    if cached_response:
        logger.info(f"Using cached response for {sentiment} reply")
        return cached_response
    
    try:
        text = api_client.generate_text(ai_headers, user_prompt)
        if text:
            cache_response(user_prompt, text)
            logger.info(f"Generated {sentiment} reply with {AI_PROVIDER} API")
            return text
    except Exception as e:
        logger.error(f"Failed to generate {sentiment} reply with {AI_PROVIDER} API: {e}")
    
    # Enhanced fallback template selection based on sentiment
    template_category = 'positive' if sentiment.startswith(('very_positive', 'positive')) else \
                       'negative' if sentiment.startswith(('very_negative', 'negative')) else \
                       'question' if sentiment.startswith('question') else \
                       'neutral'
    
    template = get_random_template('reply', template_category)
    logger.warning(f"Using template fallback for {sentiment} reply due to API failure")
    return template

def get_prompt_for_content_type(content_type, theme=None):
    """Return the task-specific user prompt for the content type."""
    current_month = datetime.utcnow().month
    season = get_season(current_month)

    # These prompts are now just the *user* part of the request
    # The base persona is handled by api_client.generate_text
    base_user_prompts = {
        'pun': "Create a witty rucking pun. Focus on rhymes with ruck/rucking or rucking concepts. Make it smile-worthy for fellow ruckers. IMPORTANT: Response strictly under 240 characters.",
        
        'challenge': f"Generate a {season}-themed rucking challenge. It should encourage community participation with specific, measurable goals. IMPORTANT: Response strictly under 240 characters.",
        
        'health_benefits': f"Write a post about the {theme if theme else 'general'} health and fitness benefits of rucking. Include ONE specific fact or statistic and cite the study. IMPORTANT: Response strictly under 240 characters.",
        
        'poll': "Create an engaging poll about rucking preferences. Include specific options related to gear, training methods, or favorite rucking locations. IMPORTANT: Response strictly under 240 characters, clearly formatted as a poll question with options.",
        
        'meme': "Describe a relatable rucking meme. Focus on training struggles or gear preparations with a specific humorous scenario. Output text for a meme. IMPORTANT: Response strictly under 240 characters.",
        
        # generate_session_post handles its own more complex prompt for shoutouts based on session data.
        # generate_map_post_text handles its own complex prompt.
        # generate_reply handles its own complex prompt.
        # UGC comments are also handled by a different function/prompt in scheduler.py (engage_with_posts)
    }

    if content_type == 'theme': # Legacy handling, should ideally be phased out or mapped better
        content_type = 'health_benefits'
    
    # Fallback to a generic engagement prompt if content_type not in base_user_prompts
    # This is important because 'shoutout', 'ugc', 'map_post' are handled by other functions
    # and 'select_content_type' might still return them.
    user_prompt = base_user_prompts.get(content_type, f"Write an engaging tweet about {content_type if content_type else 'rucking'}. Include a call to action or a question. #GoRuckYourself")
    return user_prompt

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
    
    post_text = ""

    # Check if either OpenAI or Groq key is available, prioritizing OpenAI
    # AI_PROVIDER from config.py should guide this more cleanly
    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        effective_api_source = "OpenAI"
    else:
        effective_api_source = None 
        logger.warning(f"No suitable AI API key found (checked OpenAI). Map post text generation will use fallback.")

    if effective_api_source:
        try:
            session_details_for_prompt = f"""
Distance: {distance} miles
Duration: {duration}
Pace: {pace}/mile
Weight: {weight}kg
Elevation gain: {elevation}m"""

            location_string_for_prompt = ""
            if city and state and country:
                location_string_for_prompt = f"{city}, {state}, {country}"
            elif city and country:
                location_string_for_prompt = f"{city}, {country}"
            elif city:
                location_string_for_prompt = f"{city}"
            else:
                location_string_for_prompt = "an awesome spot"

            # Adjust example location for prompt clarity if it's the generic fallback
            example_location_display = location_string_for_prompt
            if location_string_for_prompt == "an awesome spot":
                example_location_display = "the great outdoors"

            # This is the user_prompt for the map post text generation
            user_prompt = f"""The ruck session was at/in '{location_string_for_prompt}'. Write a short, engaging start to a tweet (around 140-160 characters before stats are added) about this session.
Your opening should naturally mention the location, calling out anything interesting or well-known about it if possible (e.g. 'Rucking through the historic streets of Madrid...' or 'Conquered some hills in sunny California!') or quote a famous author or movie line about that place if possible
Then, make ONE keen, specific observation about the ruck itself based on these details:
{session_details_for_prompt}    

Focus on something impressive, unusual, or notable in the session. Keep the tone enthusiastic and inspiring. End with ONE relevant hashtag like #GetRucky, #RuckLife or #Rucking.
Example for a known location: 'Solid {distance}-mile ruck through {example_location_display}! That {weight}kg pack is no joke. Great discipline! #GetRucky'
Example for an unknown location: 'Kicking off the day with a Ruck of the day from an awesome spot! {distance} miles logged. That commitment is inspiring! #RuckLife'
Output ONLY the tweet text (location intro, observation, and one hashtag), ready for detailed stats (like 🏃‍♂️, ⏱️ etc.) to be appended by the system.
"""

            logger.info(f"{effective_api_source} User Prompt for map post: {user_prompt}")
            ai_headers = api_client.initialize_ai_client() # Ensure headers are fresh for the active provider
            generated_text = api_client.generate_text(ai_headers, user_prompt) # Pass only the user_prompt
            
            logger.info(f"Generated {effective_api_source} text for map post: {generated_text}")

            if generated_text and len(generated_text) > 10:
                post_text = generated_text.strip()
            else:
                logger.warning(f"{effective_api_source} generation failed or response too short, using fallback.")
                default_location_intro = "Ruck of the day"
                if location_string_for_prompt != "an awesome spot":
                    default_location_intro = f"Ruck of the day from {location_string_for_prompt}."
                post_text = f"{default_location_intro} Showing some serious dedication! #GetRucky"

        except Exception as e:
            logger.error(f"Error generating {effective_api_source} text for map post: {e}")
            default_location_intro = "Ruck of the day"
            if city:
                location_string_fallback = f"{city}, {state}, {country}" if city and state and country else f"{city}, {country}" if city and country else city
                if location_string_fallback:
                    default_location_intro = f"Ruck of the day from {location_string_fallback}."
            post_text = f"{default_location_intro} Pushing limits and loving it! #GetRucky"
    else:
        # This block executes if no API key was found (already logged above)
        default_location_intro = "Ruck of the day"
        location_string_for_fallback = ""
        if city and state and country:
            location_string_for_fallback = f"{city}, {state}, {country}"
        elif city and country:
            location_string_for_fallback = f"{city}, {country}"
        elif city:
            location_string_for_fallback = f"{city}"

        if location_string_for_fallback:
            default_location_intro = f"Ruck of the day from {location_string_for_fallback}."
        post_text = f"{default_location_intro} Another session in the books! #GetRucky"

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
    max_length = 276  # Allow more room for map posts, actual truncation near 280 happens elsewhere if needed by Twitter.
    if len(combined_text) > max_length:
        # Calculate how much space is needed for essential information
        essential_length = len(post_text) + 20  # Allow some minimal space for most important stats
        
        # If essential content alone is too long, trim the post_text while preserving XAI observation
        if essential_length > max_length:
            # Preserve as much of the observation as possible
            available_space = max_length - len(location_text) - 10  # Reserve some space for stats
            if available_space > 30:  # Ensure we have reasonable space for an observation
                post_text = location_text + post_text[len(location_text):len(location_text)+available_space-3] + "..."
            else:
                # If space is too tight, just use location with minimal text
                post_text = location_text.strip() + " Great job!"
            
            # Add most critical stats only (distance)
            if distance and float(distance) > 0:
                combined_text = f"{post_text} 🏃‍♂️ {distance}mi"
            else:
                combined_text = post_text
        else:
            # We can keep the full post_text but need to trim stats
            # Sort stats by importance: distance, duration, weight, pace, elevation
            priority_stats = []
            remaining_space = max_length - len(post_text) - 1  # -1 for the space
            
            if distance and float(distance) > 0:
                stat = f"🏃‍♂️ {distance} miles"
                if len(stat) <= remaining_space:
                    priority_stats.append(stat)
                    remaining_space -= len(stat) + 2  # +2 for ", "
            
            if remaining_space > 15 and duration and duration != "0h" and duration != "N/A":
                stat = f"⏱️ {duration}"
                if len(stat) <= remaining_space:
                    priority_stats.append(stat)
                    remaining_space -= len(stat) + 2
            
            if remaining_space > 10 and weight and float(weight) > 0:
                stat = f"🎒 {weight}kg"
                if len(stat) <= remaining_space:
                    priority_stats.append(stat)
                    remaining_space -= len(stat) + 2
            
            if remaining_space > 10 and pace and pace != "N/A":
                stat = f"⚡ {pace}/mi"
                if len(stat) <= remaining_space:
                    priority_stats.append(stat)
                    remaining_space -= len(stat) + 2
            
            if remaining_space > 15 and elevation and float(elevation) > 10:
                stat = f"⛰️ {elevation}m gain"
                if len(stat) <= remaining_space:
                    priority_stats.append(stat)
            
            # Join prioritized stats
            priority_stats_text = ", ".join(priority_stats)
            combined_text = f"{post_text} {priority_stats_text}"
    
    return combined_text 