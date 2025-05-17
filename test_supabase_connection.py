#!/usr/bin/env python
# test_supabase_connection.py - Script to test Supabase connection

import logging
import os
from datetime import datetime
from supabase_client import initialize_supabase_client, get_recent_ruck_sessions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test Supabase connection and data retrieval."""
    try:
        # Check for required environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        # Print the URL being used (with masked key)
        supabase_url = os.getenv('SUPABASE_URL')
        logger.info(f"Connecting to Supabase at: {supabase_url}")
        
        # Initialize client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Test connection by fetching recent sessions
        logger.info("Fetching recent ruck sessions...")
        sessions = get_recent_ruck_sessions(supabase_client, limit=5)
        
        if not sessions:
            logger.warning("No ruck sessions found. Check that your database has data.")
            # Try listing the available tables
            logger.info("Checking available tables...")
            try:
                response = supabase_client.rpc("get_public_tables").execute()
                if response.data:
                    logger.info(f"Available public tables: {response.data}")
                else:
                    logger.warning("Could not retrieve list of tables")
            except Exception as table_error:
                logger.error(f"Error checking tables: {table_error}")
            
            return True  # Connection worked even if no data
            
        # Display the sessions
        logger.info(f"Successfully fetched {len(sessions)} sessions:")
        for i, session in enumerate(sessions, 1):
            user_id = session.get('user_id', 'no user')
            distance = session.get('distance', 'unknown distance')
            created_at = session.get('created_at', 'unknown time')
            session_id = session.get('id', 'no id')
            logger.info(f"  {i}. User ID: {user_id}, Distance: {distance} miles on {created_at} (ID: {session_id})")
            
        return True
    except Exception as e:
        logger.error(f"Error testing Supabase connection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Supabase connection test {'succeeded' if success else 'failed'}") 