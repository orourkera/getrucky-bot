import os
import logging
import tweepy
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# X API credentials from environment variables
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET')

# Rucking app API credentials
APP_API_TOKEN = os.getenv('APP_API_TOKEN')
APP_API_URL = 'https://rucking-app.herokuapp.com/api/sessions'

# xAI API credentials
XAI_API_KEY = os.getenv('XAI_API_KEY')
XAI_API_URL = 'https://api.x.ai/v1/chat/completions'  # Updated to a more specific endpoint based on typical xAI API structure

def test_x_api():
    """Test connectivity to the X API."""
    logger.info(f"X_API_KEY set: {bool(X_API_KEY)}")
    logger.info(f"X_API_SECRET set: {bool(X_API_SECRET)}")
    logger.info(f"X_ACCESS_TOKEN set: {bool(X_ACCESS_TOKEN)}")
    logger.info(f"X_ACCESS_TOKEN_SECRET set: {bool(X_ACCESS_TOKEN_SECRET)}")
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        logger.error("X API credentials are not fully set in environment variables.")
        return False

    try:
        auth = tweepy.OAuthHandler(X_API_KEY, X_API_SECRET)
        auth.set_access_token(X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        # Test by verifying credentials instead of fetching user info due to access restrictions
        creds = api.verify_credentials()
        logger.info(f"Successfully connected to X API. Verified credentials for user: {creds.screen_name}")
        return True
    except tweepy.errors.TweepyException as e:
        logger.error(f"Failed to connect to X API: {str(e)}")
        return False

def test_app_api():
    """Test connectivity to the rucking app API."""
    logger.info(f"APP_API_TOKEN set: {bool(APP_API_TOKEN)}")
    if not APP_API_TOKEN:
        logger.error("Rucking app API token is not set in environment variables.")
        return False

    try:
        headers = {'Authorization': f'Bearer {APP_API_TOKEN}'}
        response = requests.get(APP_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("Successfully connected to rucking app API.")
            return True
        else:
            logger.error(f"Failed to connect to rucking app API. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to rucking app API: {str(e)}")
        return False

def test_xai_api():
    """Test connectivity to the xAI API."""
    logger.info(f"XAI_API_KEY set: {bool(XAI_API_KEY)}")
    if not XAI_API_KEY:
        logger.error("xAI API key is not set in environment variables.")
        return False

    try:
        headers = {'Authorization': f'Bearer {XAI_API_KEY}', 'Content-Type': 'application/json'}
        payload = {'model': 'grok-2-latest', 'messages': [{'role': 'user', 'content': 'Test connectivity'}], 'stream': False, 'temperature': 0.7}
        response = requests.post(XAI_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("Successfully connected to xAI API.")
            logger.info(f"Response: {response.json()}")
            return True
        else:
            logger.error(f"Failed to connect to xAI API. Status code: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to xAI API: {str(e)}")
        return False

def main():
    """Run connectivity tests for all APIs."""
    logger.info("Starting API connectivity tests...")
    
    x_result = test_x_api()
    app_result = test_app_api()
    xai_result = test_xai_api()
    
    logger.info("API Connectivity Test Results:")
    logger.info(f"X API: {'PASS' if x_result else 'FAIL'}")
    logger.info(f"Rucking App API: {'PASS' if app_result else 'FAIL'}")
    logger.info(f"xAI API: {'PASS' if xai_result else 'FAIL'}")
    
    if all([x_result, app_result, xai_result]):
        logger.info("All API connectivity tests passed!")
    else:
        logger.warning("One or more API connectivity tests failed. Check logs for details.")

if __name__ == '__main__':
    main() 