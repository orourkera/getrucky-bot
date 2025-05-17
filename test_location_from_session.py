#!/usr/bin/env python
# test_location_from_session.py - Script to test location retrieval from a specific session

import logging
import sys
import os
from supabase_client import initialize_supabase_client, get_location_from_session, geocode_coordinates

# Configure logging with more detail
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_location(session_id=None):
    """Test location retrieval for a specific session ID."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Use provided session ID or default to a known one
        if not session_id and len(sys.argv) > 1:
            session_id = sys.argv[1]
        
        if not session_id:
            session_id = "643"  # Default to the session used in the tweet
        
        logger.info(f"Testing location retrieval for session ID: {session_id}")
        
        # First, get the session details
        try:
            int_session_id = int(session_id)
            logger.info(f"Getting session details for session ID: {int_session_id}")
            session_response = supabase_client.table('ruck_session').select('*').eq('id', int_session_id).execute()
            
            if session_response.data:
                session = session_response.data[0]
                logger.info(f"Session details: {session}")
                user_id = session.get('user_id')
                start_time = session.get('started_at')
                end_time = session.get('completed_at')
                
                logger.info(f"Session user_id: {user_id}")
                logger.info(f"Session started_at: {start_time}")
                logger.info(f"Session completed_at: {end_time}")
            else:
                logger.warning(f"No session found with ID {session_id}")
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
        
        # Now check location_point table structure
        logger.info("Checking location_point table structure")
        try:
            # Get a sample entry to see column names
            sample_response = supabase_client.table('location_point').select('*').limit(1).execute()
            if sample_response.data:
                sample_point = sample_response.data[0]
                logger.info(f"Location point columns: {list(sample_point.keys())}")
            else:
                logger.warning("No location points found at all")
                
            # Try to query for all location points
            all_points = supabase_client.table('location_point').select('*').execute()
            logger.info(f"Total location points in database: {len(all_points.data) if all_points.data else 0}")
            
            # If we have any points, show the first few
            if all_points.data:
                for i, point in enumerate(all_points.data[:5]):
                    logger.info(f"Sample point {i+1}: {point}")
                    
                # Try to find any points that match our session ID
                matching_points = [p for p in all_points.data if str(p.get('session_id', '')) == str(session_id)]
                logger.info(f"Found {len(matching_points)} location points with session_id = {session_id}")
                
                if matching_points:
                    logger.info(f"First matching point: {matching_points[0]}")
                else:
                    logger.warning(f"No location points found for session {session_id}")
        except Exception as e:
            logger.error(f"Error checking location_point table: {e}")
        
        # Direct query for location points for this session
        logger.info(f"Directly querying location points for session ID {int_session_id}")
        location_response = supabase_client.table('location_point').select('*').eq('session_id', int_session_id).execute()
        logger.info(f"Direct query result: {len(location_response.data) if location_response.data else 0} points found")
        
        # Now use our standard function
        logger.info("Using get_location_from_session function")
        location = get_location_from_session(supabase_client, session_id)
        logger.info(f"Location result: {location}")
        
        # Check geocoding directly
        logger.info("Testing geocoding function directly with sample coordinates")
        test_coords = [
            (40.7128, -74.0060),  # New York
            (37.7749, -122.4194)  # San Francisco
        ]
        
        for lat, lon in test_coords:
            logger.info(f"Geocoding coordinates: {lat}, {lon}")
            geo_result = geocode_coordinates(lat, lon)
            logger.info(f"Geocoding result: {geo_result}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing location retrieval: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_location()
    print(f"Location test {'succeeded' if success else 'failed'}") 