#!/usr/bin/env python
# test_map_post.py - Script to test the ruck session tweet functionality

import logging
import os
from datetime import datetime
import tempfile
from supabase_client import initialize_supabase_client, get_session_with_map, format_session_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_map_post_text(session_data):
    """Generate text for a map post based on session data."""
    # Extract data for the tweet
    distance = session_data.get('distance', '0')
    duration = session_data.get('duration', '0h')
    pace = session_data.get('pace', 'N/A')
    weight = session_data.get('ruck_weight', '0')
    
    # Use a fixed format as requested: "Ruck of the day from <city>, <state>, <country>. Great job rucker!"
    city = "Austin"  # Default placeholder
    state = "TX"     # Default placeholder
    country = "USA"  # Default placeholder
    
    # Create the tweet text in the requested format
    post_text = f"Ruck of the day from {city}, {state}, {country}. Great job rucker!"
    
    # Add some stats as a second line
    stats = f"{distance} miles in {duration} with {weight}kg"
    
    # Combine the required format with some useful stats
    combined_text = f"{post_text} {stats}"
    
    return combined_text

def main():
    """Test generating a map-based tweet."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Fetch a single ruck session
        logger.info("Fetching recent ruck session...")
        response = supabase_client.table('ruck_session').select('*').limit(1).execute()
        
        if not response.data:
            logger.error("No ruck sessions found")
            return False
        
        session_data = response.data[0]
        logger.info(f"Found session ID: {session_data['id']}")
        
        # Format session data
        formatted_data = format_session_data(session_data)
        logger.info(f"Formatted session data: {formatted_data}")
        
        # Generate tweet text
        post_text = generate_map_post_text(formatted_data)
        
        # Add a timestamp for uniqueness
        timestamp = datetime.now().strftime('%H:%M:%S')
        post_text = f"{post_text} [Test {timestamp}]"
        
        logger.info("\n" + "="*80)
        logger.info("SAMPLE TWEET WITH MAP:")
        logger.info("="*80)
        logger.info(post_text)
        logger.info("(Map would be attached as an image)")
        logger.info("="*80 + "\n")
        
        logger.info(f"Tweet length: {len(post_text)} characters")
        if len(post_text) > 280:
            logger.warning(f"Tweet is too long! Max is 280 characters, current is {len(post_text)}")
            logger.info(f"Truncated version: {post_text[:277]}...")
        
        return True
    except Exception as e:
        logger.error(f"Error testing map post: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Map post test {'succeeded' if success else 'failed'}") 