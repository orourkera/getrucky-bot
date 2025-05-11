# api_client.py

import tweepy
import requests
import logging
from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, APP_API_TOKEN, XAI_API_KEY, get_config

logger = logging.getLogger(__name__)

# X API Client
def initialize_x_client():
    """Initialize and return X API client with OAuth 1.0a authentication using v2 API."""
    try:
        # Initialize with OAuth 1.0a for full access
        client = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        
        # Verify credentials by fetching user info
        try:
            me = client.get_me()
            if me.data:
                logger.info(f"X API client initialized successfully with OAuth 1.0a for user @{me.data.username}")
                return client
            else:
                raise Exception("Failed to get user info")
        except Exception as e:
            logger.error(f"Failed to verify OAuth 1.0a credentials: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Failed to initialize X API client: {e}")
        raise

def initialize_readonly_client():
    """Initialize and return a read-only X API client using Bearer token."""
    try:
        bearer_token = get_config('X_BEARER_TOKEN')
        if not bearer_token:
            raise Exception("No Bearer token available")
            
        client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
        # Verify credentials by fetching user info
        try:
            me = client.get_me()
            if me.data:
                logger.info(f"Read-only X API client initialized successfully with Bearer token for user @{me.data.username}")
                return client
            else:
                raise Exception("Failed to get user info")
        except Exception as e:
            logger.error(f"Failed to verify Bearer token credentials: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to initialize read-only X API client: {e}")
        return None

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

def reply_to_tweet(client, tweet_id, text, media=None):
    """Reply to a specific tweet with optional media."""
    try:
        if media:
            # Media upload still uses v1.1 API, need separate handling
            auth = tweepy.OAuthHandler(X_API_KEY, X_API_SECRET)
            auth.set_access_token(X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True)
            media_upload = api.media_upload(filename=media)
            media_id = media_upload.media_id_string
            result = client.create_tweet(text=text, media_ids=[media_id], in_reply_to_tweet_id=tweet_id)
        else:
            result = client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
        logger.info(f"Replied to tweet {tweet_id}: {text[:50]}...")
        return result.data['id']
    except Exception as e:
        logger.error(f"Error replying to tweet {tweet_id}: {e}")
        raise

def like_tweet(client, tweet_id):
    """Like a specific tweet."""
    try:
        client.like(tweet_id)
        logger.info(f"Liked tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error liking tweet {tweet_id}: {e}")
        return False

def retweet(client, tweet_id):
    """Retweet a specific tweet."""
    try:
        client.retweet(tweet_id)
        logger.info(f"Retweeted tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error retweeting tweet {tweet_id}: {e}")
        return False

def search_tweets(client, query, min_likes=10):
    """Search recent tweets for a query, filter by minimum likes."""
    try:
        # Use read-only client for search if available
        readonly_client = initialize_readonly_client()
        search_client = readonly_client if readonly_client else client
        
        tweets = search_client.search_recent_tweets(query=query, max_results=100)
        if not tweets.data:
            return []
            
        filtered_tweets = []
        for tweet in tweets.data:
            # Get like count using read-only client
            tweet_data = search_client.get_tweet(tweet.id, tweet_fields=['public_metrics'])
            if tweet_data.data and tweet_data.data.public_metrics['like_count'] >= min_likes:
                filtered_tweets.append(tweet)
                
        logger.info(f"Searched for '{query}': found {len(filtered_tweets)} tweets with >= {min_likes} likes")
        return filtered_tweets
    except Exception as e:
        logger.error(f"Error searching tweets for '{query}': {e}")
        return []

def get_user_followers(client, username):
    """Fetch follower count for a user."""
    try:
        # Use read-only client if available
        readonly_client = initialize_readonly_client()
        search_client = readonly_client if readonly_client else client
        
        user = search_client.get_user(username=username, user_fields=['public_metrics'])
        if not user.data:
            return 0
            
        follower_count = user.data.public_metrics['followers_count']
        logger.info(f"Fetched follower count for {username}: {follower_count}")
        return follower_count
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