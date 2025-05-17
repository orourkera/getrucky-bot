#!/usr/bin/env python
# check_location_point.py - Script to check location points for sessions

import logging
import sys
import os
import json
import requests
from supabase_client import initialize_supabase_client, get_location_from_session, geocode_coordinates

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_location_points(session_id=None):
    """Check location points for a specific session ID or sample from the database."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Print Supabase URL for debugging
        supabase_url = os.getenv('SUPABASE_URL', '')
        logger.info(f"Using Supabase URL: {supabase_url}")
        
        # Test direct API access to diagnose permission issues
        try:
            from supabase import Client
            
            api_key = os.getenv('SUPABASE_KEY', '')
            # Only show first 8 characters for security
            if api_key:
                logger.info(f"API Key prefix: {api_key[:8]}...")
            else:
                logger.warning("No API key found in environment")
            
            # Make a direct request to the location_point table
            direct_url = f"{supabase_url}/rest/v1/location_point?select=*&limit=1"
            headers = {
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Making direct request to: {direct_url}")
            response = requests.get(direct_url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Direct request successful, got {len(response.json())} records")
            else:
                logger.error(f"Direct request failed: {response.status_code} - {response.text}")
        except Exception as direct_error:
            logger.error(f"Error making direct request: {direct_error}")
        
        # Use provided session ID or default to 643
        if not session_id and len(sys.argv) > 1:
            session_id = sys.argv[1]
        
        if not session_id:
            session_id = '643'  # Default to known good session
        
        logger.info(f"Checking location points for session ID: {session_id}")
        
        # Try to get location points for the session
        response = supabase_client.table('location_point').select('*').eq('session_id', int(session_id)).limit(5).execute()
        
        if not response.data:
            logger.warning(f"No location points found for session {session_id}")
            return False
            
        logger.info(f"Found {len(response.data)} location points for session {session_id}")
        
        # Print the first few points
        for i, point in enumerate(response.data[:2]):
            logger.info(f"Point {i+1}: lat={point.get('latitude')}, lon={point.get('longitude')}")
        
        # Test geocoding with the first point
        first_point = response.data[0]
        latitude = first_point.get('latitude')
        longitude = first_point.get('longitude')
        
        if latitude and longitude:
            logger.info(f"Geocoding coordinates: {latitude}, {longitude}")
            location = geocode_coordinates(latitude, longitude)
            logger.info(f"Geocoded location: {location}")
            
            # Check if location has data
            if not location.get('city') and not location.get('state') and not location.get('country'):
                logger.warning("Geocoding returned empty location data!")
                
                # Test with a known location as a sanity check
                test_lat, test_lon = 40.7128, -74.0060  # New York City
                logger.info(f"Testing geocoding with known coordinates (NYC): {test_lat}, {test_lon}")
                test_location = geocode_coordinates(test_lat, test_lon)
                logger.info(f"Test geocoded location: {test_location}")
        
        # Test the get_location_from_session function
        logger.info(f"Testing get_location_from_session with session {session_id}...")
        location_result = get_location_from_session(supabase_client, session_id)
        logger.info(f"Location from session: {location_result}")
        
        # Test creating a full post
        from content_generator import generate_map_post_text
        
        # Get the full session data
        session_response = supabase_client.table('ruck_session').select('*').eq('id', int(session_id)).execute()
        if session_response.data:
            from supabase_client import format_session_data
            formatted_data = format_session_data(session_response.data[0])
            
            # Add location information
            formatted_data['city'] = location_result.get('city', '')
            formatted_data['state'] = location_result.get('state', '')
            formatted_data['country'] = location_result.get('country', '')
            
            logger.info(f"Formatted session data: {formatted_data}")
            
            # Generate post text
            post_text = generate_map_post_text(formatted_data)
            logger.info(f"Generated post text: {post_text}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking location points: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_location_points()
    print(f"Location point check {'succeeded' if success else 'failed'}") 