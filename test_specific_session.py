#!/usr/bin/env python
# test_specific_session.py - Script to test a post with manually provided session data

import logging
import os
import sys
from datetime import datetime
import content_generator
import api_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test posting with manually provided session data."""
    try:
        # Check if we should test with XAI
        use_xai = "--with-xai" in sys.argv
        if use_xai:
            logger.info("Testing with XAI observation generation")
            # Temporarily set XAI_API_KEY in environment for testing
            if 'XAI_API_KEY' not in os.environ and os.environ.get('GROQ_API_KEY'):
                os.environ['XAI_API_KEY'] = os.environ.get('GROQ_API_KEY')
                logger.info("Using GROQ_API_KEY as XAI_API_KEY for testing")
            
            if 'XAI_API_KEY' not in os.environ:
                logger.warning("XAI_API_KEY not set in environment, will not use XAI observations")
        
        # Create a manually defined session data object for ID 684
        session_data = {
            'id': 684,
            'user_id': 'manual-test-user',
            'duration_seconds': 98987,  # From the screenshot
            'ruck_weight_kg': 0,        # From the screenshot
            'distance_km': 5.0,         # Example value
            'started_at': '2025-05-15T10:00:00',  # Example value
            'status': 'completed'
        }
        
        # Format session data for display
        formatted_data = {
            'user': session_data.get('user_id', 'RuckStar'),
            'distance': str(float(session_data.get('distance_km', 5.0)) * 0.621371),  # Convert km to miles
            'duration': format_duration(session_data.get('duration_seconds', 0)),
            'total_distance': str(float(session_data.get('distance_km', 5.0)) * 0.621371),
            'streak': '0',
            'session_id': session_data.get('id', ''),
            'date': session_data.get('started_at', datetime.now().isoformat()),
            'ruck_weight': session_data.get('ruck_weight_kg', 0),
            'status': session_data.get('status', ''),
            'calories': 500,  # Example value
            'elevation_gain': 100,  # Example value
            'avg_heart_rate': 130,  # Example value
            'pace': calculate_pace(session_data.get('duration_seconds', 0), session_data.get('distance_km', 5.0))
        }
        
        logger.info(f"Using manually created session data for ID: {session_data['id']}")
        logger.info(f"Formatted session data: {formatted_data}")
        
        # If testing with XAI and no default observation is provided, manually generate one
        if use_xai and 'XAI_API_KEY' in os.environ:
            try:
                # Format data for the observation prompt
                session_details = f"""
                Distance: {formatted_data['distance']} miles
                Duration: {formatted_data['duration']}
                Pace: {formatted_data['pace']}/mile
                Weight: {formatted_data['ruck_weight']}kg
                Elevation gain: {formatted_data['elevation_gain']}m
                """
                
                # Create a prompt for observation testing
                prompt = f"""You are a rucking enthusiast and coach analyzing a ruck session. 
                Make ONE keen, specific observation about this ruck (less than 100 characters):
                {session_details}
                
                Focus on something impressive, unusual, or notable about this specific session.
                KEEP YOUR OBSERVATION VERY BRIEF."""
                
                # Initialize xAI client
                xai_headers = api_client.initialize_xai_client()
                
                # Generate the observation
                observation = api_client.generate_text(xai_headers, prompt)
                logger.info(f"Generated XAI observation for testing: {observation}")
                
                # Print the observation separately
                print("\n" + "="*80)
                print("GENERATED OBSERVATION:")
                print("="*80)
                print(observation)
                print("="*80 + "\n")
                
            except Exception as e:
                logger.error(f"Error generating XAI observation: {e}")
                logger.error("Will use default post text without observation")
        
        # Generate post text
        post_text = content_generator.generate_map_post_text(formatted_data)
        
        # Add uniqueness (timestamp)
        current_time = datetime.now().strftime('%H:%M')
        post_text = f"{post_text} [{current_time}]"
        
        # Ensure it's within character limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        # Preview tweet
        print("\n" + "="*80)
        print("TWEET PREVIEW:")
        print("="*80)
        print(post_text)
        print("="*80 + "\n")
        
        logger.info(f"Tweet content: {post_text}")
        logger.info(f"Tweet length: {len(post_text)} characters")
        
        return True
    except Exception as e:
        logger.error(f"Error creating test post: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def format_duration(seconds):
    """Format duration in seconds to a human-readable string."""
    if not seconds:
        return "0m"
        
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def calculate_pace(duration_seconds, distance_km):
    """Calculate pace in min/mile format."""
    if not duration_seconds or not distance_km or float(distance_km) <= 0:
        return "N/A"
        
    # Convert to minutes per mile
    minutes_per_km = duration_seconds / 60 / float(distance_km)
    minutes_per_mile = minutes_per_km * 1.60934
    
    # Format as min:sec
    minutes = int(minutes_per_mile)
    seconds = int((minutes_per_mile - minutes) * 60)
    
    return f"{minutes}:{seconds:02d}"

if __name__ == "__main__":
    success = main()
    print(f"Test post creation {'succeeded' if success else 'failed'}") 