#!/usr/bin/env python
# check_table_structure.py - Script to check the table structure

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
            logger.error("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY environment variables.")
            return False
        
        # Initialize Supabase client
        logger.info(f"Connecting to Supabase at: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
        
        # Fetch a sample record from the location_point table to see columns
        logger.info("Fetching sample record from location_point table...")
        response = supabase.table('location_point').select('*').limit(1).execute()
        
        if response.data:
            logger.info("Sample location_point record:")
            logger.info(f"Columns: {list(response.data[0].keys())}")
            for key, value in response.data[0].items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("No records found in location_point table.")
            
        # Try to fetch column information using RPC if possible
        logger.info("Trying to get column information from information_schema...")
        try:
            # Using RPC to run a custom SQL query to get column information
            query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'location_point'
            ORDER BY ordinal_position;
            """
            # Note: This will only work if your Supabase permissions allow this query
            column_response = supabase.rpc('run_sql', {'query': query}).execute()
            
            if column_response.data:
                logger.info("Column information:")
                for column in column_response.data:
                    logger.info(f"  {column['column_name']}: {column['data_type']}")
            else:
                logger.warning("Could not retrieve column information via RPC.")
        except Exception as e:
            logger.warning(f"Could not retrieve column information via RPC: {e}")
            
        # Fetch a sample record from the ruck_session table as well
        logger.info("Fetching sample record from ruck_session table...")
        session_response = supabase.table('ruck_session').select('*').limit(1).execute()
        
        if session_response.data:
            logger.info("Sample ruck_session record:")
            logger.info(f"Columns: {list(session_response.data[0].keys())}")
            for key, value in session_response.data[0].items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("No records found in ruck_session table.")
            
        return True
    except Exception as e:
        logger.error(f"Error checking table structure: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Table structure check {'succeeded' if success else 'failed'}") 