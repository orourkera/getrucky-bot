# scheduler.py

import random
import logging
from datetime import datetime, time
import content_generator
import api_client
from config import get_post_times, POST_FREQUENCY

logger = logging.getLogger(__name__)


def schedule_posts(scheduler, x_client, app_client, xai_headers):
    """Schedule regular and session-based posts for the day."""
    try:
        num_posts = random.choice(POST_FREQUENCY)  # Randomly select number of posts (5-10)
        selected_times = get_post_times()[:num_posts]
        
        # Schedule regular content posts (3-8)
        regular_posts = max(3, num_posts - 2)  # Ensure at least 3 regular posts, reserve 2 for session posts if possible
        for i, time_tuple in enumerate(selected_times[:regular_posts]):
            hour, minute = time_tuple
            scheduler.add_job(
                post_regular_content,
                'cron',
                hour=hour,
                minute=minute,
                args=[x_client, xai_headers],
                id=f'regular_post_{hour}_{minute}'
            )
            logger.info(f"Scheduled regular post at {hour}:{minute:02d} UTC")
        
        # Schedule session-based posts (2-3 if possible)
        session_posts = min(3, num_posts - regular_posts + 2)  # Aim for 2-3 session posts
        session_times = selected_times[regular_posts:regular_posts + session_posts]
        for i, time_tuple in enumerate(session_times):
            hour, minute = time_tuple
            scheduler.add_job(
                post_session_content,
                'cron',
                hour=hour,
                minute=minute,
                args=[x_client, app_client, xai_headers],
                id=f'session_post_{hour}_{minute}_{i}'
            )
            logger.info(f"Scheduled session post at {hour}:{minute:02d} UTC")
        
        logger.info(f"Scheduled {num_posts} total posts for the day")
    except Exception as e:
        logger.error(f"Error scheduling posts: {e}")

def schedule_engagement(scheduler, x_client, xai_headers):
    """Schedule engagement tasks to run every 2 hours."""
    try:
        scheduler.add_job(
            engage_with_posts,
            'interval',
            hours=2,
            args=[x_client, xai_headers],
            id='engagement_task'
        )
        logger.info("Scheduled engagement task to run every 2 hours")
    except Exception as e:
        logger.error(f"Error scheduling engagement task: {e}")

def post_regular_content(x_client, xai_headers):
    """Generate and post regular content."""
    try:
        content_type, theme = content_generator.select_content_type()
        post_text = content_generator.generate_post(xai_headers, content_type, theme)
        if len(post_text) > 280:
            post_text = post_text[:277] + '...'
        tweet_id = api_client.post_tweet(x_client, post_text)
        logger.info(f"Posted regular content (type: {content_type}): {post_text[:50]}...")
        return tweet_id
    except Exception as e:
        logger.error(f"Error posting regular content: {e}")
        return None

def post_session_content(x_client, app_client, xai_headers):
    """Fetch ruck session data and post about it with enhanced achievement tracking."""
    try:
        sessions = api_client.get_ruck_sessions(app_client)
        if sessions:
            # Sort sessions by achievements to prioritize more significant ones
            sessions.sort(key=lambda s: (
                float(s.get('distance', 0)) >= 10,  # Double-digit distance
                float(s.get('total_distance', 0)) >= 100,  # 100-mile milestone
                int(s.get('streak', 0)) >= 7,  # 7-day streak
                float(s.get('distance', 0))  # Then by distance
            ), reverse=True)
            
            # Try to find a session with achievements first
            session = next((s for s in sessions if any([
                float(s.get('distance', 0)) >= 10,
                float(s.get('total_distance', 0)) >= 100,
                int(s.get('streak', 0)) >= 7
            ])), sessions[0])  # Fallback to first session if none have achievements
            
            # Add total distance and streak if not present
            if 'total_distance' not in session:
                session['total_distance'] = str(float(session.get('distance', 0)))
            if 'streak' not in session:
                session['streak'] = '0'
            
            post_text = content_generator.generate_session_post(xai_headers, session)
            if len(post_text) > 280:
                post_text = post_text[:277] + '...'
            tweet_id = api_client.post_tweet(x_client, post_text)
            logger.info(f"Posted session content for {session.get('user', 'user')}: {post_text[:50]}...")
            return tweet_id
        else:
            logger.warning("No ruck sessions available for posting")
            # Fallback to regular content with seasonal theme
            return post_regular_content(x_client, xai_headers)
    except Exception as e:
        logger.error(f"Error posting session content: {e}")
        # Fallback to regular content on error
        return post_regular_content(x_client, xai_headers)

def engage_with_posts(x_client, xai_headers):
    """Engage with posts by liking, retweeting, and commenting."""
    from config import SEARCH_TERMS, LIKE_PROBABILITY, RETWEET_ACCOUNTS, MIN_FOLLOWERS
    from analytics import store_engagement_action, get_engagement_actions
    from datetime import datetime, timedelta
    try:
        query = random.choice(SEARCH_TERMS)
        tweets = api_client.search_tweets(x_client, query)
        engagement_count = {'liked': 0, 'retweeted': 0, 'commented': 0}
        
        # Check weekly comment limit (aim for ~10 per week)
        start_of_week = (datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())).isoformat()
        engagement_actions = get_engagement_actions(start_of_week)
        weekly_comments = sum(1 for action in engagement_actions if action['action'] == 'comment')
        comment_limit_reached = weekly_comments >= 10
        
        for tweet in tweets:
            tweet_id = tweet.id
            username = tweet.user.screen_name
            
            # Like with 90% probability
            if random.random() < LIKE_PROBABILITY:
                if api_client.like_tweet(x_client, tweet_id):
                    engagement_count['liked'] += 1
                    store_engagement_action(tweet_id, 'like')
            
            # Check retweet eligibility
            followers = api_client.get_user_followers(x_client, username)
            if username in RETWEET_ACCOUNTS or followers > MIN_FOLLOWERS:
                if api_client.retweet(x_client, tweet_id):
                    engagement_count['retweeted'] += 1
                    store_engagement_action(tweet_id, 'retweet')
            
            # Cross-posting comment (limit to 10 per week using database counter)
            if not comment_limit_reached:
                prompt = "Generate a comment for a rucking post, promoting @getrucky, <280 characters."
                comment_text = content_generator.get_cached_response(prompt)
                if not comment_text:
                    comment_text = api_client.generate_text(xai_headers, prompt)
                    content_generator.cache_response(prompt, comment_text)
                if comment_text and len(comment_text) <= 280:
                    if api_client.reply_to_tweet(x_client, tweet_id, comment_text):
                        engagement_count['commented'] += 1
                        store_engagement_action(tweet_id, 'comment')
                        weekly_comments += 1
                        if weekly_comments >= 10:
                            comment_limit_reached = True
        
        logger.info(f"Engagement results: Liked {engagement_count['liked']}, Retweeted {engagement_count['retweeted']}, Commented {engagement_count['commented']}")
        return engagement_count
    except Exception as e:
        logger.error(f"Error during engagement with posts: {e}")
        return {'liked': 0, 'retweeted': 0, 'commented': 0} 