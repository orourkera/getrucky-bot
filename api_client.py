# api_client.py

import tweepy
import requests
import logging
from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, APP_API_TOKEN, XAI_API_KEY

logger = logging.getLogger(__name__)

# X API Client
def initialize_x_client():
    """Initialize and return X API client with OAuth 1.0a authentication using v2 API."""
    try:
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET
        )
        # Verify credentials by fetching user info
        client.get_me()
        logger.info("X API client initialized successfully with v2 API")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize X API client: {e}")
        raise

def post_tweet(client, text, media=None):
    """Post a tweet with optional media using v2 API."""
    try:
        if media:
            # Media upload still uses v1.1 API, need separate handling
            auth = tweepy.OAuthHandler(X_API_KEY, X_API_SECRET)
            auth.set_access_token(X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            media_upload = api.media_upload(filename=media)
            media_id = media_upload.media_id_string
            result = client.create_tweet(text=text, media_ids=[media_id])
        else:
            result = client.create_tweet(text=text)
        logger.info(f"Posted tweet: {text[:50]}...")
        return result.data['id']
    except Exception as e:
        logger.error(f"Error posting tweet: {e}")
        raise

def reply_to_tweet(api, tweet_id, text, media=None):
    """Reply to a specific tweet with optional media."""
    try:
        if media:
            result = api.update_status_with_media(status=text, filename=media, in_reply_to_status_id=tweet_id)
        else:
            result = api.update_status(status=text, in_reply_to_status_id=tweet_id)
        logger.info(f"Replied to tweet {tweet_id}: {text[:50]}...")
        return result.id
    except Exception as e:
        logger.error(f"Error replying to tweet {tweet_id}: {e}")
        raise

def like_tweet(api, tweet_id):
    """Like a specific tweet."""
    try:
        api.create_favorite(tweet_id)
        logger.info(f"Liked tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error liking tweet {tweet_id}: {e}")
        return False

def retweet(api, tweet_id):
    """Retweet a specific tweet."""
    try:
        api.retweet(tweet_id)
        logger.info(f"Retweeted tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error retweeting tweet {tweet_id}: {e}")
        return False

def search_tweets(api, query, min_likes=10):
    """Search recent tweets for a query, filter by minimum likes."""
    try:
        tweets = api.search_tweets(q=query, lang="en", result_type="recent", count=100)
        filtered_tweets = [tweet for tweet in tweets if tweet.favorite_count >= min_likes]
        logger.info(f"Searched for '{query}': found {len(filtered_tweets)} tweets with >= {min_likes} likes")
        return filtered_tweets
    except Exception as e:
        logger.error(f"Error searching tweets for '{query}': {e}")
        return []

def get_user_followers(api, username):
    """Fetch follower count for a user."""
    try:
        user = api.get_user(screen_name=username)
        logger.info(f"Fetched follower count for {username}: {user.followers_count}")
        return user.followers_count
    except Exception as e:
        logger.error(f"Error fetching followers for {username}: {e}")
        return 0

# Rucking App API Client
def initialize_app_client():
    """Initialize and return rucking app API client."""
    try:
        headers = {'Authorization': f'Bearer {APP_API_TOKEN}'}
        logger.info("Rucking app API client initialized")
        return headers
    except Exception as e:
        logger.error(f"Failed to initialize app API client: {e}")
        raise

def get_ruck_sessions(headers, limit=10, min_distance=5):
    """Fetch ruck sessions from app API with minimum distance filter."""
    try:
        response = requests.get(
            f"https://rucking-app.herokuapp.com/api/sessions?limit={limit}&min_distance={min_distance}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        sessions = response.json()
        logger.info(f"Fetched {len(sessions)} ruck sessions")
        return sessions
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching ruck sessions: {e}")
        return []

def get_session_details(headers, session_id):
    """Fetch detailed data for a specific ruck session."""
    try:
        response = requests.get(
            f"https://rucking-app.herokuapp.com/api/sessions/{session_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        session_data = response.json()
        logger.info(f"Fetched details for session {session_id}")
        return session_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching session details for {session_id}: {e}")
        return {}

# xAI API Client
def initialize_xai_client():
    """Initialize and return xAI API client."""
    try:
        headers = {'Authorization': f'Bearer {XAI_API_KEY}', 'Content-Type': 'application/json'}
        logger.info("xAI API client initialized")
        return headers
    except Exception as e:
        logger.error(f"Failed to initialize xAI API client: {e}")
        raise

def generate_text(headers, prompt, max_length=280):
    """Generate text using xAI API with a given prompt."""
    try:
        payload = {
            'prompt': prompt,
            'max_tokens': 100,
            'temperature': 0.9
        }
        response = requests.post(
            "https://x.ai/api",
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        generated_text = response.json().get('choices', [{}])[0].get('text', '').strip()
        if len(generated_text) > max_length:
            generated_text = generated_text[:max_length].rsplit(' ', 1)[0] + '...'
        logger.info(f"Generated text for prompt: {prompt[:30]}...")
        return generated_text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating text with xAI API: {e}")
        return "" 