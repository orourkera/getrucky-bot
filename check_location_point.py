#!/usr/bin/env python
# check_location_point.py - Script to check the location_point table structure

import logging
import os
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check the structure of the location_point table."""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials.")
            return False
        
        # Initialize Supabase client
        logger.info(f"Connecting to Supabase at: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
        
        # First try to get all column names without filtering or ordering
        logger.info("Checking location_point table basic query...")
        try:
            response = supabase.table('location_point').select('*').limit(1).execute()
            logger.info(f"Basic query response: {response.data}")
        except Exception as e:
            logger.error(f"Error on basic query: {e}")
        
        # Try with various session IDs
        session_ids = [641, 642, 643, 647]
        for session_id in session_ids:
            logger.info(f"Querying location_point for session_id = {session_id}")
            try:
                response = supabase.table('location_point').select('*').eq('session_id', session_id).execute()
                
                if response.data:
                    logger.info(f"Found {len(response.data)} location points")
                    # Print column names from the first record
                    logger.info(f"Location point columns: {list(response.data[0].keys())}")
                    # Print first record
                    logger.info(f"First record: {response.data[0]}")
                    return True
                else:
                    logger.info(f"No location points found for session {session_id}")
            except Exception as e:
                logger.error(f"Error querying location_point for session {session_id}: {e}")
        
        # If basic queries fail, try to check the table existence and its columns
        logger.info("Trying to get table structure information...")
        try:
            query = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'location_point';
            """
            response = supabase.rpc('run_sql_query', {'query': query}).execute()
            logger.info(f"Column info response: {response.data}")
        except Exception as e:
            logger.error(f"Error getting column info: {e}")
        
        logger.warning("Could not determine location_point table structure")
        return False
    except Exception as e:
        logger.error(f"Error checking table structure: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Location point check {'succeeded' if success else 'failed'}") 