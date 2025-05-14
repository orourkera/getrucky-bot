# api_client.py

import tweepy
import requests
from requests_oauthlib import OAuth1
import logging
import time
from typing import Optional
from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, APP_API_TOKEN, XAI_API_KEY, get_config
import datetime
import os

logger = logging.getLogger(__name__)

# Cache for client verification
_client_verification_cache = {
    'timestamp': 0,
    'client': None,
    'username': None
}

def validate_oauth_credentials():
    """Validate that OAuth 1.0a credentials are in the correct format."""
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        raise ValueError("Missing required OAuth 1.0a credentials")
    
    # API Key should be a string of reasonable length
    if not isinstance(X_API_KEY, str) or len(X_API_KEY) < 10:
        raise ValueError("Invalid API Key format")
    
    # API Secret should be a string of reasonable length
    if not isinstance(X_API_SECRET, str) or len(X_API_SECRET) < 10:
        raise ValueError("Invalid API Secret format")
    
    # Access Token should be a string of reasonable length
    if not isinstance(X_ACCESS_TOKEN, str) or len(X_ACCESS_TOKEN) < 10:
        raise ValueError("Invalid Access Token format")
    
    # Access Token Secret should be a string of reasonable length
    if not isinstance(X_ACCESS_TOKEN_SECRET, str) or len(X_ACCESS_TOKEN_SECRET) < 10:
        raise ValueError("Invalid Access Token Secret format")

# X API Client
def initialize_x_client(max_retries=3, retry_delay=5, verify=True):
    """Initialize X API client with rate limit tracking and verification caching."""
    global _client_verification_cache
    
    # Check if we have a cached client that's less than 10 minutes old
    current_time = time.time()
    if _client_verification_cache['client'] and (current_time - _client_verification_cache['timestamp']) < 600:
        logger.info(f"Using cached client for @{_client_verification_cache['username']}")
        return _client_verification_cache['client']
    
    try:
        logger.info("Initializing X client (attempt 1/3)")
        client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_SECRET'),
            wait_on_rate_limit=True
        )
        
        # Only verify if requested and cache is expired
        if verify:
            logger.info("Verifying OAuth 1.0a credentials by fetching user info")
            try:
                user = client.get_me()
                if not user.data:
                    raise Exception("Failed to verify credentials")
                
                # Cache the verified client
                _client_verification_cache = {
                    'timestamp': current_time,
                    'client': client,
                    'username': user.data.username
                }
                logger.info(f"Successfully authenticated as @{user.data.username}")
            except tweepy.errors.TooManyRequests as e:
                logger.warning(f"Rate limit hit during verification: {e}")
                # If we hit rate limit, use the client anyway but don't cache it
                return client
        else:
            logger.info("Skipping client verification as requested")
            
        return client
    except Exception as e:
        logger.error(f"Failed to initialize X client: {e}")
        if max_retries > 0:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            return initialize_x_client(max_retries - 1, retry_delay * 2, verify)
        raise

def initialize_readonly_client():
    """Initialize and return a read-only X API client using Bearer token."""
    try:
        bearer_token = get_config('X_BEARER_TOKEN')
        if not bearer_token:
            logger.warning("No Bearer token available for read-only client.")
            return None
            
        client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
        logger.info("Read-only X API client initialized with Bearer token (verification skipped).")
        return client
            
    except Exception as e:
        logger.error(f"Failed to initialize read-only X API client: {e}")
        return None

def log_rate_limits(response):
    """Log rate limit information from response headers."""
    if not hasattr(response, 'headers'):
        return
        
    headers = response.headers
    rate_limit_info = {
        'limit': headers.get('x-rate-limit-limit', 'N/A'),
        'remaining': headers.get('x-rate-limit-remaining', 'N/A'),
        'reset': headers.get('x-rate-limit-reset', 'N/A')
    }
    
    # Convert reset timestamp to human-readable time
    if rate_limit_info['reset'] != 'N/A':
        reset_time = datetime.datetime.utcfromtimestamp(int(rate_limit_info['reset']))
        rate_limit_info['reset_time'] = reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    logger.info(f"Rate Limit Status: {rate_limit_info}")
    
    # If we're close to the limit, log a warning
    if rate_limit_info['remaining'] != 'N/A':
        remaining = int(rate_limit_info['remaining'])
        if remaining < 10:
            logger.warning(f"Rate limit nearly exceeded! {remaining} calls remaining, resets at {rate_limit_info.get('reset_time', 'N/A')}")

def post_tweet(client, text, media=None, max_retries=2):
    """Post a tweet with optional media using v2 API."""
    for attempt in range(max_retries + 1):
        try:
            if media:
                # Media upload still uses v1.1 API, need separate handling
                auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_SECRET)
                auth.set_access_token(X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
                api = tweepy.API(auth, wait_on_rate_limit=True)
                media_upload = api.media_upload(filename=media)
                media_id = media_upload.media_id_string
                result = client.create_tweet(text=text, media_ids=[media_id])
            else:
                result = client.create_tweet(text=text)
            log_rate_limits(result)
            logger.info(f"Posted tweet: {text[:50]}...")
            return result.data['id']
        except tweepy.errors.Unauthorized as unauth:
            logger.error(f"Unauthorized error posting tweet (attempt {attempt+1}/{max_retries+1}): {unauth}")
            if hasattr(unauth, 'response') and unauth.response is not None:
                logger.error(f"Response: {unauth.response.status_code} - {unauth.response.text}")
            # Don't retry unauthorized - credentials are wrong
            raise
        except tweepy.errors.TooManyRequests as rate:
            logger.warning(f"Rate limit hit posting tweet (attempt {attempt+1}/{max_retries+1}): {rate}")
            if attempt < max_retries:
                wait_time = 60 * (attempt + 1)  # Exponential backoff: 1 minute, then 2 minutes
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            logger.error(f"Error posting tweet (attempt {attempt+1}/{max_retries+1}): {e}")
            if attempt < max_retries:
                time.sleep(30)  # Wait 30 seconds before retry
            else:
                raise

def reply_to_tweet(client, tweet_id, text, media=None, max_retries=2):
    """Reply to a specific tweet with optional media."""
    for attempt in range(max_retries + 1):
        try:
            if media:
                # Media upload still uses v1.1 API, need separate handling
                auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_SECRET)
                auth.set_access_token(X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
                api = tweepy.API(auth, wait_on_rate_limit=True)
                media_upload = api.media_upload(filename=media)
                media_id = media_upload.media_id_string
                result = client.create_tweet(text=text, media_ids=[media_id], in_reply_to_tweet_id=tweet_id)
            else:
                result = client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
            logger.info(f"Replied to tweet {tweet_id}: {text[:50]}...")
            return result.data['id']
        except tweepy.errors.Unauthorized as unauth:
            logger.error(f"Unauthorized error replying to tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {unauth}")
            if hasattr(unauth, 'response') and unauth.response is not None:
                logger.error(f"Response: {unauth.response.status_code} - {unauth.response.text}")
            # Don't retry unauthorized - credentials are wrong
            raise
        except tweepy.errors.TooManyRequests as rate:
            logger.warning(f"Rate limit hit replying to tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {rate}")
            if attempt < max_retries:
                wait_time = 60 * (attempt + 1)  # Exponential backoff: 1 minute, then 2 minutes
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            logger.error(f"Error replying to tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {e}")
            if attempt < max_retries:
                time.sleep(30)  # Wait 30 seconds before retry
            else:
                raise

def like_tweet(client, tweet_id, max_retries=2):
    """Like a specific tweet."""
    for attempt in range(max_retries + 1):
        try:
            result = client.like(tweet_id)
            logger.info(f"Liked tweet {tweet_id}")
            return True
        except tweepy.errors.TooManyRequests as rate:
            logger.warning(f"Rate limit hit liking tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {rate}")
            if attempt < max_retries:
                wait_time = 30 * (attempt + 1)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                return False
        except Exception as e:
            logger.error(f"Error liking tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {e}")
            if attempt < max_retries:
                time.sleep(15)
            else:
                return False

def retweet(client, tweet_id, max_retries=2):
    """Retweet a specific tweet."""
    for attempt in range(max_retries + 1):
        try:
            result = client.retweet(tweet_id)
            logger.info(f"Retweeted tweet {tweet_id}")
            return True
        except tweepy.errors.TooManyRequests as rate:
            logger.warning(f"Rate limit hit retweeting tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {rate}")
            if attempt < max_retries:
                wait_time = 30 * (attempt + 1)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                return False
        except Exception as e:
            logger.error(f"Error retweeting tweet {tweet_id} (attempt {attempt+1}/{max_retries+1}): {e}")
            if attempt < max_retries:
                time.sleep(15)
            else:
                return False

def search_tweets(client, query, min_likes=10):
    """Search recent tweets with rate limit tracking."""
    try:
        logger.info(f"API CALL: search_recent_tweets for query '{query}'")
        response = client.search_recent_tweets(query=query, max_results=100, tweet_fields=['public_metrics'])
        log_rate_limits(response)
        
        if not response.data:
            return []
            
        filtered_tweets = [tweet for tweet in response.data 
                          if hasattr(tweet, 'public_metrics') 
                          and tweet.public_metrics.get('like_count', 0) >= min_likes]
        logger.info(f"Searched for '{query}': found {len(filtered_tweets)} tweets with >= {min_likes} likes")
        return filtered_tweets
    except Exception as e:
        logger.error(f"Error searching tweets for '{query}': {e}")
        return []

# Simple in-memory cache for user followers (per process run)
_user_followers_cache = {}
def get_user_followers(client, username):
    """Fetch follower count with rate limit tracking."""
    try:
        if username in _user_followers_cache:
            logger.info(f"Cache HIT for followers of {username}")
            return _user_followers_cache[username]
            
        logger.info(f"API CALL: get_user for username '{username}'")
        readonly_client = initialize_readonly_client()
        search_client = readonly_client if readonly_client else client
        response = search_client.get_user(username=username, user_fields=['public_metrics'])
        log_rate_limits(response)
        
        if not response.data:
            return 0
            
        follower_count = response.data.public_metrics['followers_count']
        _user_followers_cache[username] = follower_count
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

def check_rate_limit_status():
    """Check and log the current Twitter/X API rate limit status for the authenticated user."""
    auth = requests.auth.OAuth1(
        os.getenv('TWITTER_API_KEY'),
        os.getenv('TWITTER_API_SECRET'),
        os.getenv('TWITTER_ACCESS_TOKEN'),
        os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    )
    url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        data = response.json()
        resources = data.get('resources', {})
        logger.info("Current Twitter/X API Rate Limits:")
        for category, endpoints in resources.items():
            for endpoint, limits in endpoints.items():
                reset_time = datetime.datetime.utcfromtimestamp(limits['reset']).strftime('%Y-%m-%d %H:%M:%S UTC')
                logger.info(f"{endpoint}: {limits['remaining']} remaining (limit {limits['limit']}), resets at {reset_time}")
        return resources
    except Exception as e:
        logger.error(f"Error checking rate limit status: {e}")
        return None

# Make the function available at module level
__all__ = [
    'initialize_x_client',
    'initialize_readonly_client',
    'post_tweet',
    'reply_to_tweet',
    'like_tweet',
    'retweet',
    'search_tweets',
    'get_user_followers',
    'initialize_app_client',
    'get_ruck_sessions',
    'get_session_details',
    'initialize_xai_client',
    'generate_text',
    'check_rate_limit_status'  # Add this to exports
] 