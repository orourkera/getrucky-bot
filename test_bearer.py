#!/usr/bin/env python3
# test_bearer.py

import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test posting a single tweet using the v2 API with bearer token."""
    logger.info("Starting direct X API v2 test with bearer token")
    
    try:
        # Get bearer token from environment variable
        # Note: You'll need to set this in Heroku with:
        # heroku config:set X_BEARER_TOKEN=your_bearer_token -a getrucky-bot
        bearer_token = os.environ.get('X_BEARER_TOKEN')
        
        if not bearer_token:
            logger.error("No bearer token found in environment variables")
            return False
            
        logger.info(f"Bearer token: {bearer_token[:5]}...{bearer_token[-5:]}")
        
        # Set up authorization header
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        
        # Post tweet using v2 API
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": "Testing with bearer token! Ruck it Up with @getrucky! 🥾 #GetRucky"}
        
        response = requests.post(url, json=payload, headers=headers)
        
        # Check response
        if response.status_code == 201:
            logger.info(f"Successfully posted tweet: {response.json()}")
            return True
        else:
            logger.error(f"Failed to post tweet. Status code: {response.status_code}, Response: {response.text}")
            
            # Try a GET request to verify the token is working
            me_url = "https://api.twitter.com/2/users/me"
            me_response = requests.get(me_url, headers=headers)
            logger.info(f"GET /me test: Status code: {me_response.status_code}, Response: {me_response.text}")
            
            return False
    except Exception as e:
        logger.error(f"Error in direct v2 API test with bearer token: {e}")
        return False

if __name__ == "__main__":
    main() 