#!/usr/bin/env python3
# test_tweet.py

import os
import requests
import logging
from requests_oauthlib import OAuth1Session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test posting a single tweet using the v2 API directly."""
    logger.info("Starting direct X API v2 test")
    
    try:
        # Get credentials from environment variables
        consumer_key = os.environ.get('X_API_KEY')
        consumer_secret = os.environ.get('X_API_SECRET')
        access_token = os.environ.get('X_ACCESS_TOKEN')
        access_token_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
        
        # Print credentials (masked for security)
        logger.info(f"Consumer Key: {consumer_key[:5]}...{consumer_key[-5:]}")
        logger.info(f"Access Token: {access_token[:5]}...{access_token[-5:]}")
        
        # Create OAuth1 session
        oauth = OAuth1Session(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        # Post tweet using v2 API
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": "Testing the X API v2 with direct OAuth! Ruck it Up with @getrucky! 🥾 #GetRucky"}
        
        response = oauth.post(url, json=payload)
        
        # Check response
        if response.status_code == 201:
            logger.info(f"Successfully posted tweet: {response.json()}")
            return True
        else:
            logger.error(f"Failed to post tweet. Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error in direct v2 API test: {e}")
        return False

if __name__ == "__main__":
    main() 