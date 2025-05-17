#!/usr/bin/env python
# test_location_role.py - Test location points access with different roles

import logging
import os
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_location_role():
    """Test location retrieval with different Supabase roles."""
    try:
        # Check environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_KEY')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        logger.info(f"SUPABASE_URL exists: {bool(supabase_url)}")
        logger.info(f"SUPABASE_KEY exists: {bool(anon_key)}")
        logger.info(f"SUPABASE_SERVICE_ROLE_KEY exists: {bool(service_role_key)}")
        
        results = []
        
        # Test with anon key
        if supabase_url and anon_key:
            logger.info("Testing with anon key...")
            client = create_client(supabase_url, anon_key)
            
            # First test getting the ruck_session
            session_id = 643
            logger.info(f"Querying ruck_session with ID {session_id}")
            response = client.table('ruck_session').select('*').eq('id', session_id).execute()
            logger.info(f"Found {len(response.data)} session records")
            
            # Try querying location_point table directly
            logger.info("Querying location_point table with anon key")
            try:
                # Check if the table is accessible at all
                response = client.table('location_point').select('*').limit(10).execute()
                logger.info(f"location_point table contains {len(response.data)} records")
                results.append(f"Anon key can access location_point table, found {len(response.data)} records")
                
                # Try to query for a specific session
                response = client.table('location_point').select('*').eq('session_id', session_id).execute()
                logger.info(f"Found {len(response.data)} location points for session {session_id}")
                results.append(f"Anon key found {len(response.data)} location points for session {session_id}")
                
                # Add a message stating key permission
                results.append("PERMISSIONS: Anon key CAN access location_point table")
            except Exception as e:
                logger.error(f"Error querying location_point with anon key: {e}")
                results.append(f"ERROR with anon key: {str(e)}")
                results.append("PERMISSIONS: Anon key CANNOT access location_point table")
        
        # Test with service role key if available
        if supabase_url and service_role_key:
            logger.info("Testing with service role key...")
            service_client = create_client(supabase_url, service_role_key)
            
            # Test querying location_point table directly
            logger.info("Querying location_point table with service role key")
            try:
                # Check if the table is accessible
                response = service_client.table('location_point').select('*').limit(10).execute()
                logger.info(f"location_point table contains {len(response.data)} records")
                results.append(f"Service role key can access location_point table, found {len(response.data)} records")
                
                # Try to query for a specific session
                session_id = 643
                response = service_client.table('location_point').select('*').eq('session_id', session_id).execute()
                logger.info(f"Found {len(response.data)} location points for session {session_id}")
                results.append(f"Service role key found {len(response.data)} location points for session {session_id}")
                
                # List all schemas
                logger.info("Checking all available schemas")
                try:
                    # Use SQL query to list all tables
                    query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                    response = service_client.rpc('run_sql_query', {'query': query}).execute()
                    if response.data:
                        table_names = [row.get('table_name') for row in response.data]
                        logger.info(f"Available tables: {table_names}")
                        results.append(f"Available tables: {table_names}")
                except Exception as schema_error:
                    logger.error(f"Error querying schemas: {schema_error}")
            except Exception as e:
                logger.error(f"Error querying location_point with service role key: {e}")
                results.append(f"ERROR with service role key: {str(e)}")
        
        # Print summary of results
        logger.info("\n=== TEST RESULTS ===")
        for result in results:
            logger.info(result)
        
        return True
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_location_role()
    print(f"Location role test {'succeeded' if success else 'failed'}") 