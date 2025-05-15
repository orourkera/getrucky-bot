#!/usr/bin/env python
# test_xai_api.py

import logging
import os
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_xai_api():
    """Test the xAI API connection directly."""
    logger.info("Testing xAI API connection directly")
    
    # Get the API key
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        logger.error("XAI_API_KEY environment variable not set")
        return False
    
    logger.info(f"Using API key starting with: {api_key[:5]}...")
    
    # Set up headers
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test prompt
    prompt = "Generate a short message about the benefits of rucking, <50 characters"
    
    # API payload
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.9
    }
    
    try:
        logger.info("Making direct call to xAI API...")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        # Check the response status
        if response.status_code == 200:
            logger.info(f"API call succeeded with status {response.status_code}")
            response_json = response.json()
            if 'choices' in response_json and len(response_json['choices']) > 0:
                content = response_json['choices'][0]['message']['content']
                logger.info(f"Generated text: {content}")
                return True
            else:
                logger.error(f"Unexpected API response: {response_json}")
                return False
        else:
            logger.error(f"API call failed with status {response.status_code}")
            logger.error(f"Error response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error calling xAI API: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_xai_api()
    logger.info(f"xAI API test {'succeeded' if success else 'failed'}") 