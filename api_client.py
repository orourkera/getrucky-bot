# api_client.py

import tweepy
import requests
import logging
import time
from typing import Optional
from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, APP_API_TOKEN, XAI_API_KEY, get_config
import datetime

logger = logging.getLogger(__name__)

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
def initialize_x_client(max_retries=3, retry_delay=5, verify: Optional[bool] = False, wait_on_rate_limit: bool = True):
    """Initialize and return X API client with OAuth 1.0a authentication using v2 API."""
    for attempt in range(max_retries):
        try:
            # Validate credentials first
            validate_oauth_credentials()
            
            logger.info(f"Initializing X client (attempt {attempt + 1}/{max_retries})")
            
            # Initialize with OAuth 1.0a for full access
            client = tweepy.Client(
                consumer_key=X_API_KEY,
                consumer_secret=X_API_SECRET,
                access_token=X_ACCESS_TOKEN,
                access_token_secret=X_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=wait_on_rate_limit
            )
            
            # Optionally verify credentials
            if verify:
                try:
                    logger.info("Verifying OAuth 1.0a credentials by fetching user info")
                    me = client.get_me()
                    if me and hasattr(me, 'data') and me.data:
                        logger.info(f"X API client initialized successfully with OAuth 1.0a for user @{me.data.username} (ID: {me.data.id})")
                        return client
                    else:
                        logger.warning("Failed to get user info during client verification - empty response")
                        raise Exception("Failed to get user info - empty response")
                        
                except tweepy.errors.Unauthorized as unauth_error:
                    logger.error(f"Unauthorized error during client verification: {unauth_error}")
                    if hasattr(unauth_error, 'response') and unauth_error.response is not None:
                        logger.error(f"Response: {unauth_error.response.status_code} - {unauth_error.response.text}")
                    raise
                except tweepy.errors.TooManyRequests as rate_error:
                    logger.warning(f"Rate limit hit during client verification: {rate_error}")
                    # Don't fail completely, just wait and retry
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                except Exception as verify_error:
                    logger.error(f"Error verifying client credentials: {verify_error}")
                    if hasattr(verify_error, 'response') and verify_error.response is not None:
                        logger.error(f"Response: {verify_error.response.status_code} - {verify_error.response.text}")
                    raise
                # end verify block
            else:
                # No verification requested
                logger.info("X API client created without credential verification (verify=False)")
                return client
                
        except Exception as e:
            logger.error(f"Failed to initialize X API client on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All attempts to initialize X API client failed")
                raise
    
    # If we get here, all attempts failed
    raise Exception(f"Failed to initialize X API client after {max_retries} attempts")

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

def check_rate_limit_status():
    """Check and log the current Twitter/X API rate limit status for the authenticated user."""
    auth = requests.auth.OAuth1(
        X_API_KEY,
        X_API_SECRET,
        X_ACCESS_TOKEN,
        X_ACCESS_TOKEN_SECRET
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