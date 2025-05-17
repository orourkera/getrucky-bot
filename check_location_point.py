#!/usr/bin/env python
# check_location_point.py - Script to check location points for sessions

import logging
import sys
import os
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
        
        # Use provided session ID or list some samples
        if not session_id and len(sys.argv) > 1:
            session_id = sys.argv[1]
        
        if session_id:
            logger.info(f"Checking location points for session ID: {session_id}")
            # Query the location_point table for this session
            str_session_id = str(session_id)
            response = supabase_client.table('location_point').select('*').eq('session_id', str_session_id).limit(5).execute()
            
            if not response.data:
                logger.warning(f"No location points found for session {session_id}")
                return False
                
            logger.info(f"Found {len(response.data)} location points for session {session_id}")
            for i, point in enumerate(response.data[:5]):
                logger.info(f"Point {i+1}: lat={point.get('latitude')}, lon={point.get('longitude')}")
                
            # Try geocoding the first point
            first_point = response.data[0]
            latitude = first_point.get('latitude')
            longitude = first_point.get('longitude')
            
            if latitude and longitude:
                logger.info(f"Geocoding coordinates: {latitude}, {longitude}")
                location = geocode_coordinates(latitude, longitude)
                logger.info(f"Geocoded location: {location}")
            
            # Use the get_location_from_session function
            logger.info(f"Using get_location_from_session for session {session_id}...")
            location = get_location_from_session(supabase_client, session_id)
            logger.info(f"Result from get_location_from_session: {location}")
        else:
            # Sample some sessions with location points
            logger.info("Listing sample sessions with location points...")
            response = supabase_client.table('location_point').select('session_id').order('created_at', desc=True).limit(10).execute()
            
            if not response.data:
                logger.warning("No location points found in the database")
                return False
                
            session_ids = list(set([point.get('session_id') for point in response.data if point.get('session_id')]))
            logger.info(f"Sessions with location points: {session_ids}")
            
            # Get some sample coordinates for testing geocoding
            logger.info("Testing geocoding with sample coordinates...")
            test_coordinates = [
                (40.7128, -74.0060),  # New York
                (51.5074, -0.1278),   # London
                (35.6762, 139.6503),  # Tokyo
                (48.8566, 2.3522)     # Paris
            ]
            
            for lat, lon in test_coordinates:
                logger.info(f"Geocoding test coordinates: {lat}, {lon}")
                location = geocode_coordinates(lat, lon)
                logger.info(f"Geocoded location: {location}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking location points: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_location_points()
    print(f"Location point check {'succeeded' if success else 'failed'}") 