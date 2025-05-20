# scheduler.py

import random
import logging
from datetime import datetime, time
import content_generator
import api_client
from config import get_post_times, POST_FREQUENCY
import os

logger = logging.getLogger(__name__)


def schedule_posts(scheduler, x_client, app_client, ai_headers):
    """Schedule regular and session-based posts for the day, ensuring one map post attempt."""
    try:
        num_posts = random.choice(POST_FREQUENCY)  # Randomly select number of posts (5-10)
        selected_times = get_post_times()[:num_posts]
        
        if not selected_times:
            logger.warning("No post times generated, cannot schedule posts.")
            return

        # Ensure at least one post is dedicated to a session/map post attempt
        dedicated_map_post_time = selected_times.pop(0) # Take the earliest time for the map post
        hour, minute = dedicated_map_post_time
        scheduler.add_job(
            post_session_content, # This function handles map posts if session data is available
            'cron',
            hour=hour,
            minute=minute,
            args=[x_client, app_client, ai_headers],
            id=f'dedicated_map_post_{hour}_{minute}'
        )
        logger.info(f"Scheduled dedicated session/map post attempt at {hour}:{minute:02d} UTC")
        
        # Schedule remaining posts as regular content (can include other session posts via select_content_type)
        # num_posts is already reduced by 1 due to pop()
        for i, time_tuple in enumerate(selected_times): # Iterate through the remaining times
            hour, minute = time_tuple
            scheduler.add_job(
                post_regular_content,
                'cron',
                hour=hour,
                minute=minute,
                args=[x_client, ai_headers],
                id=f'regular_post_{hour}_{minute}_{i}' # Ensure unique ID
            )
            logger.info(f"Scheduled regular post at {hour}:{minute:02d} UTC")
        
        logger.info(f"Scheduled {num_posts} total posts for the day (including one dedicated session/map attempt)")
    except Exception as e:
        logger.error(f"Error scheduling posts: {e}")

def schedule_engagement(scheduler, x_client, ai_headers):
    """Schedule engagement tasks to run every 2 hours."""
    try:
        scheduler.add_job(
            engage_with_posts,
            'interval',
            hours=2,
            args=[x_client, ai_headers],
            id='engagement_task'
        )
        logger.info("Scheduled engagement task to run every 2 hours")
    except Exception as e:
        logger.error(f"Error scheduling engagement task: {e}")

def post_regular_content(x_client, ai_headers):
    """Generate and post regular content."""
    try:
        content_type, theme = content_generator.select_content_type()
        try:
            post_result = content_generator.generate_post(ai_headers, content_type, theme)
            
            # Check if this is a map post
            if isinstance(post_result, dict) and post_result.get('is_map_post'):
                return post_map_content(x_client, post_result['session_data'], post_result['map_path'])
            else:
                post_text = post_result
        except Exception as e:
            logger.error(f"Error during content generation: {e}")
            # If API fails, use template fallback
            post_text = content_generator.get_random_template('post', content_type)
            logger.warning(f"Using template fallback for {content_type} post due to xAI API error")
        
        # Final check to ensure it's under the limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        tweet_id = api_client.post_tweet(x_client, post_text)
        logger.info(f"Posted regular content (type: {content_type}): {post_text[:50]}...")
        return tweet_id
    except Exception as e:
        logger.error(f"Error posting regular content: {e}")
        return None

def post_map_content(x_client, session_data, map_path):
    """Post a ruck session with the 'Ruck of the day' format."""
    try:
        # Generate text for the map post
        post_text = content_generator.generate_map_post_text(session_data)
        
        # Final check to ensure it's under the limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        # Post the tweet (with media if available)
        if map_path and os.path.exists(map_path):
            tweet_id = api_client.post_tweet(x_client, post_text, media=map_path)
        else:
            tweet_id = api_client.post_tweet(x_client, post_text)
        
        # Log the post
        distance = session_data.get('distance', '0')
        logger.info(f"Posted 'Ruck of the day' for {distance} mile session: {post_text[:50]}...")
        
        return tweet_id
    except Exception as e:
        logger.error(f"Error posting map content: {e}")
        return None

def post_session_content(x_client, app_client, ai_headers):
    """Fetch ruck session data and post about it with enhanced achievement tracking."""
    try:
        # Try to get a session from Supabase first (if integration is available)
        try:
            from supabase_client import initialize_supabase_client, format_session_data, get_session_route_points
            
            supabase_client = initialize_supabase_client()
            
            # Get most recent session that's longer than 5 minutes (300 seconds)
            logger.info("Looking for rucks longer than 5 minutes in Supabase...")
            response = supabase_client.table('ruck_session')\
                       .select('*')\
                       .gt('duration_seconds', 300)\
                       .order('started_at', desc=True)\
                       .limit(1)\
                       .execute()
            
            if response.data:
                session_data = response.data[0]
                session_id = session_data['id']
                logger.info(f"Found Supabase session ID: {session_id} with duration {session_data.get('duration_seconds')} seconds")
                
                # Format the session data
                formatted_data = format_session_data(session_data)
                
                # Generate post text using the map post format
                post_text = content_generator.generate_map_post_text(formatted_data)
                
                # Add timestamp and format for posting
                return post_map_content(x_client, formatted_data, None)
            else:
                logger.info("No suitable Supabase sessions found, trying app API...")
        except Exception as e:
            logger.warning(f"Error using Supabase for sessions, falling back to app API: {e}")
        
        # Fall back to the legacy app API
        sessions = api_client.get_ruck_sessions(app_client)
        if sessions:
            # Filter for sessions that are at least 5 minutes (300 seconds)
            long_enough_sessions = []
            for session in sessions:
                # Convert duration to seconds if possible
                duration_str = session.get('duration', '0')
                seconds = 0
                
                try:
                    if 'h' in duration_str and 'm' in duration_str:
                        hours, mins = duration_str.split('h')
                        seconds = int(hours.strip()) * 3600 + int(mins.replace('m', '').strip()) * 60
                    elif 'h' in duration_str:
                        hours = duration_str.replace('h', '')
                        seconds = int(hours.strip()) * 3600
                    elif 'm' in duration_str:
                        mins = duration_str.replace('m', '')
                        seconds = int(mins.strip()) * 60
                except:
                    # If parsing fails, assume it's not long enough
                    seconds = 0
                
                if seconds >= 300:
                    session['duration_seconds'] = seconds
                    long_enough_sessions.append(session)
            
            if not long_enough_sessions:
                logger.warning("No sessions found that are longer than 5 minutes")
                # Fallback to regular content with seasonal theme
                return post_regular_content(x_client, ai_headers)
            
            # Sort sessions by achievements to prioritize more significant ones
            long_enough_sessions.sort(key=lambda s: (
                float(s.get('distance', 0)) >= 10,  # Double-digit distance
                float(s.get('total_distance', 0)) >= 100,  # 100-mile milestone
                int(s.get('streak', 0)) >= 7,  # 7-day streak
                float(s.get('distance', 0))  # Then by distance
            ), reverse=True)
            
            # Try to find a session with achievements first
            session = next((s for s in long_enough_sessions if any([
                float(s.get('distance', 0)) >= 10,
                float(s.get('total_distance', 0)) >= 100,
                int(s.get('streak', 0)) >= 7
            ])), long_enough_sessions[0])  # Fallback to first session if none have achievements
            
            # Add total distance and streak if not present
            if 'total_distance' not in session:
                session['total_distance'] = str(float(session.get('distance', '0')))
            if 'streak' not in session:
                session['streak'] = '0'
            
            post_text = content_generator.generate_session_post(ai_headers, session)
            
            # Final check to ensure it's under the limit
            if len(post_text) > 280:
                post_text = post_text[:276] + " ..."
                
            tweet_id = api_client.post_tweet(x_client, post_text)
            logger.info(f"Posted session content for {session.get('user', 'user')}: {post_text[:50]}...")
            return tweet_id
        else:
            logger.warning("No ruck sessions available for posting")
            # Fallback to regular content with seasonal theme
            return post_regular_content(x_client, ai_headers)
    except Exception as e:
        logger.error(f"Error posting session content: {e}")
        # Fallback to regular content on error
        return post_regular_content(x_client, ai_headers)

def engage_with_posts(x_client, ai_headers):
    """Search for and engage with relevant tweets by liking, retweeting, and commenting."""
    import random  # Import random correctly
    from config import SEARCH_TERMS, RETWEET_WHITELIST, MIN_FOLLOWER_COUNT
    from analytics import get_engagement_actions, store_engagement_action
    import datetime

    # Randomly select a search term
    query = random.choice(SEARCH_TERMS)
    
    # Fetch tweets with at least 1 like (temporarily reduced for testing)
    tweets = api_client.search_tweets(x_client, query, min_likes=1)
    
    # Track engagement actions
    liked = 0
    retweeted = 0
    commented = 0
    
    # Get weekly comment count for rate limiting
    start_of_week = datetime.datetime.now().date() - datetime.timedelta(days=datetime.datetime.now().weekday())
    try:
        weekly_comments = get_engagement_actions(start_of_week, 'comment')
        logger.info(f"Already made {len(weekly_comments)} comments this week")
    except Exception as e:
        logger.error(f"Error retrieving engagement actions: {e}")
        weekly_comments = []
    
    # Only engage with each tweet once per type of engagement
    engaged_ids = set()
    
    for tweet in tweets:
        tweet_id = tweet.id
        
        # 1. Like tweets (90% probability)
        if random.random() < 0.9 and tweet_id not in engaged_ids:
            success = api_client.like_tweet(x_client, tweet_id)
            if success:
                liked += 1
                store_engagement_action('like', tweet_id)
                engaged_ids.add(tweet_id)
        
        # 2. Retweet tweets from whitelisted accounts or with enough followers
        try:
            author_id = tweet.author_id
            author_username = x_client.get_user(id=author_id).data.username
            
            # Check if user is in whitelist or has enough followers
            in_whitelist = author_username.lower() in [name.lower() for name in RETWEET_WHITELIST]
            
            has_followers = False
            if not in_whitelist:
                follower_count = api_client.get_user_followers(x_client, author_username)
                has_followers = follower_count >= MIN_FOLLOWER_COUNT
            
            if (in_whitelist or has_followers) and tweet_id not in engaged_ids:
                success = api_client.retweet(x_client, tweet_id)
                if success:
                    retweeted += 1
                    store_engagement_action('retweet', tweet_id)
                    engaged_ids.add(tweet_id)
        except Exception as e:
            logger.error(f"Error checking author for retweet eligibility: {e}")
        
        # 3. Comment on tweets (limit to 10 per week)
        if len(weekly_comments) < 10 and tweet_id not in engaged_ids and random.random() < 0.3:
            try:
                # Construct a prompt for the AI to generate a relevant comment
                prompt = f"Write a short, engaging reply to this tweet about {query}. Be positive, friendly, and authentic. Keep it under 200 characters."
                comment_text = api_client.generate_text(ai_headers, prompt)
                
                if comment_text:
                    success = api_client.reply_to_tweet(x_client, tweet_id, comment_text)
                    if success:
                        commented += 1
                        store_engagement_action('comment', tweet_id)
                        engaged_ids.add(tweet_id)
                        # Increment weekly comments counter
                        weekly_comments.append(tweet_id)
            except Exception as e:
                logger.error(f"Error commenting on tweet {tweet_id}: {e}")
    
    logger.info(f"Engagement results: Liked {liked}, Retweeted {retweeted}, Commented {commented}")
    return {"liked": liked, "retweeted": retweeted, "commented": commented} 