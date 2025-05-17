#!/usr/bin/env python
# test_location_points.py - Script to test retrieving location points

import logging
import os
from datetime import datetime
from supabase_client import initialize_supabase_client, get_session_route_points

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test retrieving location points from Supabase."""
    try:
        # Check for required environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        # Initialize client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Get session IDs from the ruck_session table
        logger.info("Fetching session IDs...")
        response = supabase_client.table('ruck_session').select('id').limit(5).execute()
        
        if not response.data:
            logger.warning("No sessions found in the database.")
            return False
            
        session_ids = [session['id'] for session in response.data]
        logger.info(f"Found {len(session_ids)} session IDs: {session_ids}")
        
        # Try to get location points for each session
        for session_id in session_ids:
            logger.info(f"Fetching location points for session ID: {session_id}")
            route_points = get_session_route_points(supabase_client, session_id)
            
            if route_points:
                logger.info(f"Found {len(route_points)} location points for session {session_id}")
                logger.info(f"First few points: {route_points[:3]}")
                # If we found points for any session, we can test the map generation
                return True
            else:
                logger.warning(f"No location points found for session {session_id}")
        
        logger.warning("No location points found for any session. Please add location data to the database.")
        return False
            
    except Exception as e:
        logger.error(f"Error testing location points: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Location points test {'succeeded' if success else 'failed'}") 