import os
import logging
from api_client import generate_text, initialize_xai_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test xAI API connection
def test_xai_connection():
    """Test connection to xAI API with grok-3-beta model."""
    try:
        xai_headers = initialize_xai_client()
        prompt = "Explain briefly why rucking is good for fitness."
        response = generate_text(xai_headers, prompt)
        logger.info(f"Successfully connected to xAI API. Response: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to xAI API: {e}")
        return False

if __name__ == "__main__":
    if test_xai_connection():
        print("Test passed: xAI API with grok-3-beta model is working.")
    else:
        print("Test failed: Unable to connect to xAI API with grok-3-beta model.") 