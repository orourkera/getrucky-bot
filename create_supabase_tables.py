#!/usr/bin/env python
# create_supabase_tables.py - Script to add sample data to existing Supabase tables

import logging
import os
import json
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Add sample data to existing Supabase tables for the ruck map feature."""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY environment variables.")
            return False
        
        # Initialize Supabase client
        logger.info(f"Connecting to Supabase at: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
        
        # Sample route for Central Park, NYC
        central_park_route = [
            {"latitude": 40.767, "longitude": -73.9761, "point_order": 0},
            {"latitude": 40.7702, "longitude": -73.9745, "point_order": 1},
            {"latitude": 40.7736, "longitude": -73.9732, "point_order": 2},
            {"latitude": 40.7764, "longitude": -73.9719, "point_order": 3},
            {"latitude": 40.7804, "longitude": -73.9684, "point_order": 4},
            {"latitude": 40.7829, "longitude": -73.9652, "point_order": 5},
            {"latitude": 40.7818, "longitude": -73.9625, "point_order": 6},
            {"latitude": 40.7777, "longitude": -73.9647, "point_order": 7},
            {"latitude": 40.7741, "longitude": -73.9677, "point_order": 8},
            {"latitude": 40.7705, "longitude": -73.9710, "point_order": 9},
            {"latitude": 40.767, "longitude": -73.9761, "point_order": 10}
        ]
        
        # First, try to get a sample user ID
        logger.info("Checking for existing users...")
        user_response = supabase.table('user').select('id').limit(1).execute()
        user_id = None
        
        if user_response.data and len(user_response.data) > 0:
            user_id = user_response.data[0]['id']
            logger.info(f"Found existing user with ID: {user_id}")
        else:
            logger.warning("No users found in the database. Creating a sample ruck session without user_id.")
        
        # Insert a sample session
        logger.info("Inserting sample ruck session...")
        session_data = {
            "distance": 5.2,
            "duration": "1h 15m",
            "total_distance": 125.5,
            "streak": 7,
            "pace": "14:25"
        }
        
        # Add user_id if available
        if user_id:
            session_data["user_id"] = user_id
            
        try:
            response = supabase.table('ruck_session').insert(session_data).execute()
            
            if not response.data:
                logger.error("Failed to insert sample session")
                return False
                
            session_id = response.data[0]['id']
            logger.info(f"Created sample session with ID: {session_id}")
            
            # Insert route points
            logger.info("Inserting sample location points...")
            for point in central_park_route:
                point["session_id"] = session_id
                supabase.table('location_point').insert(point).execute()
                
            logger.info(f"Added {len(central_park_route)} location points to session {session_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up Supabase sample data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Supabase sample data creation {'succeeded' if success else 'failed'}") 