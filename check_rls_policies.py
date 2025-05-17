#!/usr/bin/env python
# check_rls_policies.py - Script to check RLS policies and authentication role

import logging
import os
from supabase_client import initialize_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_rls_policies():
    """Check RLS policies and current authentication role for the Supabase client."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Check environment variables
        supabase_key = os.getenv('SUPABASE_KEY', '')
        key_type = "anon key" if supabase_key.startswith("eyJ") else "service role key"
        logger.info(f"Using Supabase {key_type}")
        
        # Try to determine current role
        logger.info("Attempting to get current database role...")
        try:
            # Method 1: Try using auth.uid() function
            response = supabase_client.rpc('get_current_role').execute()
            if response.data:
                logger.info(f"Current role from RPC: {response.data}")
        except Exception as role_error:
            logger.error(f"Error getting current role via RPC: {role_error}")
            
            # Alternative approach - try a direct query that might reveal role info
            try:
                response = supabase_client.table('ruck_session').select('*').limit(1).execute()
                logger.info(f"Successfully ran a test query which suggests appropriate permissions")
            except Exception as query_error:
                logger.error(f"Error running test query: {query_error}")
                
        # Try to check RLS policies using a function or direct query
        logger.info("Checking RLS policies on location_point table...")
        try:
            # Try to query pg_policies to see policies
            response = supabase_client.rpc('get_table_policies', {'table_name': 'location_point'}).execute()
            if response.data:
                logger.info(f"Policies for location_point: {response.data}")
            else:
                logger.warning("No policies found or cannot access policy information")
        except Exception as policy_error:
            logger.error(f"Error checking policies via RPC: {policy_error}")
            logger.info("Cannot access policy information directly")
        
        # Test alternative approaches to access location data for session 643
        logger.info("Testing alternative approaches to access location data...")
        
        # Try the get_session_route_points function
        try:
            from supabase_client import get_session_route_points
            logger.info("Calling get_session_route_points for session 643...")
            route_points = get_session_route_points(supabase_client, '643')
            if route_points:
                logger.info(f"Got {len(route_points)} route points for session 643")
                logger.info(f"Sample points: {route_points[:2]}")
                
                # Check if these are dummy points
                is_dummy = any(point[0] == 40.767 and point[1] == -73.9761 for point in route_points)
                if is_dummy:
                    logger.warning("These appear to be the dummy points, not real data")
            else:
                logger.warning("No route points returned")
        except Exception as route_error:
            logger.error(f"Error getting route points: {route_error}")
        
        # Try a direct query with user_id condition
        try:
            logger.info("Getting user_id from session 643...")
            session_response = supabase_client.table('ruck_session').select('user_id').eq('id', '643').execute()
            if session_response.data:
                user_id = session_response.data[0].get('user_id')
                logger.info(f"User ID for session 643: {user_id}")
                
                logger.info(f"Trying to query location_point with user_id condition...")
                location_response = supabase_client.table('location_point').select('*').eq('user_id', user_id).limit(5).execute()
                if location_response.data:
                    logger.info(f"Found {len(location_response.data)} location points for user {user_id}")
                else:
                    logger.warning(f"No location points found for user {user_id}")
            else:
                logger.warning("Could not retrieve user_id for session 643")
        except Exception as user_query_error:
            logger.error(f"Error querying with user_id: {user_query_error}")

        return True
    except Exception as e:
        logger.error(f"Error checking RLS policies: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_rls_policies()
    print(f"RLS policy check {'succeeded' if success else 'failed'}") 