#!/usr/bin/env python
# check_database_tables.py - Script to check all available tables in Supabase

import logging
import os
from supabase_client import initialize_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_tables():
    """Check all tables in the Supabase database and test query permissions."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Check environment variables
        logger.info(f"SUPABASE_URL exists: {bool(os.getenv('SUPABASE_URL'))}")
        logger.info(f"SUPABASE_KEY exists: {bool(os.getenv('SUPABASE_KEY'))}")
        
        # List all tables using SQL query
        logger.info("Listing all tables in the database...")
        query = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public';
        """
        
        try:
            response = supabase_client.rpc('run_sql_query', {'query': query}).execute()
            if response.data:
                table_names = [row.get('table_name') for row in response.data]
                logger.info(f"Tables in database: {table_names}")
                
                # Try to query each table to check permissions
                for table_name in table_names:
                    try:
                        logger.info(f"Testing query for table: {table_name}")
                        test_response = supabase_client.table(table_name).select('*').limit(1).execute()
                        logger.info(f"Successfully queried {table_name}: Found {len(test_response.data)} records")
                        if test_response.data:
                            columns = list(test_response.data[0].keys())
                            logger.info(f"Columns in {table_name}: {columns}")
                    except Exception as table_error:
                        logger.error(f"Error querying table {table_name}: {table_error}")
            else:
                logger.warning("Failed to retrieve table names or no tables exist")
        except Exception as rpc_error:
            logger.error(f"Error executing run_sql_query RPC: {rpc_error}")
            
            # Alternative: try to directly query a few known tables
            logger.info("Trying direct queries to known tables...")
            tables_to_try = ['ruck_session', 'location_point', 'user', 'ruck_routes']
            
            for table_name in tables_to_try:
                try:
                    logger.info(f"Testing query for table: {table_name}")
                    test_response = supabase_client.table(table_name).select('*').limit(1).execute()
                    logger.info(f"Successfully queried {table_name}: Found {len(test_response.data)} records")
                    if test_response.data:
                        columns = list(test_response.data[0].keys())
                        logger.info(f"Columns in {table_name}: {columns}")
                except Exception as table_error:
                    logger.error(f"Error querying table {table_name}: {table_error}")
        
        # Specifically check session 643 in ruck_session table
        logger.info("Checking session 643 specifically...")
        try:
            session_response = supabase_client.table('ruck_session').select('*').eq('id', '643').execute()
            if session_response.data:
                logger.info(f"Session 643 exists: {session_response.data}")
            else:
                logger.warning("Session 643 not found in ruck_session table")
        except Exception as session_error:
            logger.error(f"Error checking session 643: {session_error}")
        
        # Check location_points table specifically with various names
        location_table_names = ['location_point', 'location_points', 'locationpoint', 'locationpoints', 'route_point', 'routepoint']
        
        for table_name in location_table_names:
            try:
                logger.info(f"Trying to query {table_name} table...")
                location_response = supabase_client.table(table_name).select('*').limit(5).execute()
                logger.info(f"Successfully queried {table_name}: Found {len(location_response.data)} records")
                if location_response.data:
                    logger.info(f"First record: {location_response.data[0]}")
            except Exception as loc_error:
                logger.error(f"Error querying {table_name}: {loc_error}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking database tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_database_tables()
    print(f"Database table check {'succeeded' if success else 'failed'}") 