#!/usr/bin/env python
# check_location_point.py - Script to check location points for sessions

import logging
import sys
import os
import json
import requests
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
        
        # Print Supabase URL for debugging
        supabase_url = os.getenv('SUPABASE_URL', '')
        logger.info(f"Using Supabase URL: {supabase_url}")
        
        # Test direct API access to diagnose permission issues
        try:
            from supabase import Client
            
            api_key = os.getenv('SUPABASE_KEY', '')
            # Only show first 8 characters for security
            if api_key:
                logger.info(f"API Key prefix: {api_key[:8]}...")
            else:
                logger.warning("No API key found in environment")
            
            # Make a direct request to the location_point table
            direct_url = f"{supabase_url}/rest/v1/location_point?select=*&limit=1"
            headers = {
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Making direct request to: {direct_url}")
            response = requests.get(direct_url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Direct request successful, got {len(response.json())} records")
            else:
                logger.error(f"Direct request failed: {response.status_code} - {response.text}")
        except Exception as direct_error:
            logger.error(f"Error making direct request: {direct_error}")
        
        # Explicitly check for session 643 which we know exists
        session_id = '643'
        logger.info(f"Checking location points for known session ID: {session_id}")
        
        # Try different format approaches for session_id
        formats_to_try = [
            session_id,               # String
            int(session_id) if session_id.isdigit() else session_id,  # Integer
            f"'{session_id}'",        # SQL string literal
            f"\"{session_id}\"",      # Double quoted
        ]
        
        success = False
        for format_id in formats_to_try:
            try:
                logger.info(f"Trying session_id format: {format_id} (type: {type(format_id)})")
                response = supabase_client.table('location_point').select('*').eq('session_id', format_id).limit(5).execute()
                
                if response.data:
                    logger.info(f"Success with format {format_id}! Found {len(response.data)} location points")
                    success = True
                    break
                else:
                    logger.warning(f"No data found with format {format_id}")
            except Exception as format_error:
                logger.error(f"Error with format {format_id}: {format_error}")
        
        if not success:
            # Test if the location_point table exists
            try:
                logger.info("Checking if location_point table exists...")
                # List tables
                # Note: We're using PostgreSQL's information_schema to list tables
                tables_query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                tables_response = supabase_client.rpc('pg_exec', {'query': tables_query}).execute()
                logger.info(f"Tables in database: {tables_response.data}")
                
                # Check RLS (Row Level Security) policies
                rls_query = """
                    SELECT tablename, policyname, permissive, roles, cmd, qual
                    FROM pg_policies
                    WHERE schemaname = 'public'
                """
                rls_response = supabase_client.rpc('pg_exec', {'query': rls_query}).execute()
                logger.info(f"RLS policies: {rls_response.data}")
            except Exception as schema_error:
                logger.error(f"Error checking schema: {schema_error}")
        
        return success
    except Exception as e:
        logger.error(f"Error checking location points: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_location_points()
    print(f"Location point check {'succeeded' if success else 'failed'}") 