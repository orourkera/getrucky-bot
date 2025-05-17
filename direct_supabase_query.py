#!/usr/bin/env python
# direct_supabase_query.py - Script to access Supabase via direct SQL queries

import os
import logging
import sys
import json
from supabase import create_client
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

def initialize_supabase_client():
    """Initialize and return Supabase client."""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing Supabase credentials")
        
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise

def execute_direct_sql(query, params=None):
    """Execute a direct SQL query on the Supabase database."""
    try:
        client = initialize_supabase_client()
        
        # Execute the SQL query directly using rpc
        response = client.rpc('exec_sql', {
            'query_text': query,
            'params': params or []
        }).execute()
        
        if response.error:
            logger.error(f"SQL query error: {response.error}")
            return None
        
        logger.info(f"Successfully executed SQL query")
        return response.data
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_session_by_id(session_id):
    """Get a specific session by ID using direct SQL."""
    query = """
    SELECT * FROM ruck_session 
    WHERE id = $1
    """
    
    result = execute_direct_sql(query, [session_id])
    
    if not result or not result[0]:
        logger.warning(f"No session found with ID {session_id} using direct SQL")
        return None
    
    logger.info(f"Found session with ID {session_id} using direct SQL")
    return result[0]

def get_recent_sessions(limit=10, min_duration=300):
    """Get recent sessions with minimum duration using direct SQL."""
    query = """
    SELECT * FROM ruck_session 
    WHERE duration_seconds > $1
    ORDER BY started_at DESC
    LIMIT $2
    """
    
    result = execute_direct_sql(query, [min_duration, limit])
    
    if not result:
        logger.warning(f"No sessions found with minimum duration {min_duration}s")
        return []
    
    logger.info(f"Found {len(result)} recent sessions with minimum duration {min_duration}s")
    return result

def get_session_route_points(session_id):
    """Get route points for a specific session using direct SQL."""
    query = """
    SELECT * FROM location_point
    WHERE session_id = $1
    ORDER BY created_at
    """
    
    result = execute_direct_sql(query, [session_id])
    
    if not result:
        logger.warning(f"No route points found for session {session_id}")
        return []
    
    logger.info(f"Found {len(result)} route points for session {session_id}")
    return result

def get_session_count():
    """Get the total count of sessions in the database."""
    query = "SELECT COUNT(*) FROM ruck_session"
    
    result = execute_direct_sql(query)
    
    if not result:
        return 0
    
    count = result[0]['count']
    logger.info(f"Total session count: {count}")
    return count

def get_session_id_range():
    """Get the minimum and maximum session IDs in the database."""
    query = """
    SELECT MIN(id) as min_id, MAX(id) as max_id 
    FROM ruck_session
    """
    
    result = execute_direct_sql(query)
    
    if not result:
        return None, None
    
    min_id = result[0]['min_id']
    max_id = result[0]['max_id']
    logger.info(f"Session ID range: {min_id} to {max_id}")
    return min_id, max_id

def main():
    """Main function to run database diagnostic queries."""
    try:
        # Get command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]
        else:
            command = "info"  # Default command
        
        # Execute different functions based on the command
        if command == "info":
            # Print general database information
            count = get_session_count()
            min_id, max_id = get_session_id_range()
            
            print("\n=== Supabase Database Info ===")
            print(f"Total sessions: {count}")
            print(f"Session ID range: {min_id} to {max_id}")
            print("=============================\n")
            
        elif command == "session" and len(sys.argv) > 2:
            # Get a specific session by ID
            session_id = sys.argv[2]
            session = get_session_by_id(session_id)
            
            if session:
                print(f"\n=== Session {session_id} ===")
                print(json.dumps(session, indent=2))
                print("=====================\n")
                
                # Also get route points if requested
                if len(sys.argv) > 3 and sys.argv[3] == "points":
                    points = get_session_route_points(session_id)
                    print(f"\n=== Route Points for Session {session_id} ===")
                    print(f"Found {len(points)} points")
                    if points and len(points) > 0:
                        print(f"First point: {json.dumps(points[0], indent=2)}")
                        print(f"Last point: {json.dumps(points[-1], indent=2)}")
                    print("=====================\n")
            
        elif command == "recent":
            # Get recent sessions
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            min_duration = int(sys.argv[3]) if len(sys.argv) > 3 else 300
            
            sessions = get_recent_sessions(limit, min_duration)
            
            print(f"\n=== {len(sessions)} Recent Sessions ===")
            for session in sessions:
                started = session.get('started_at', 'unknown')
                duration = session.get('duration_seconds', 0)
                distance = session.get('distance_km', 0)
                
                print(f"ID: {session['id']}, Started: {started}, Duration: {duration}s, Distance: {distance}km")
            print("=====================\n")
            
        elif command == "sql" and len(sys.argv) > 2:
            # Execute a custom SQL query
            query = sys.argv[2]
            params = sys.argv[3:] if len(sys.argv) > 3 else None
            
            result = execute_direct_sql(query, params)
            
            print("\n=== SQL Query Result ===")
            print(json.dumps(result, indent=2))
            print("=====================\n")
            
        else:
            print("\nUsage:")
            print("  python direct_supabase_query.py [command] [arguments]")
            print("\nCommands:")
            print("  info                      : Show database information")
            print("  session <id> [points]     : Get a specific session by ID (add 'points' to see route points)")
            print("  recent [limit] [min_dur]  : Get recent sessions with optional limit and minimum duration")
            print("  sql <query> [params...]   : Execute a custom SQL query with optional parameters")
            print("\nExamples:")
            print("  python direct_supabase_query.py info")
            print("  python direct_supabase_query.py session 684")
            print("  python direct_supabase_query.py session 684 points")
            print("  python direct_supabase_query.py recent 10 300")
            print("  python direct_supabase_query.py sql \"SELECT * FROM ruck_session WHERE id > $1\" 680")
        
        return True
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 