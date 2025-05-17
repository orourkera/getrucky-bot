#!/usr/bin/env python
# read_location_data.py - Script to read location data from the Supabase database

import logging
import os
import sys
import json
from supabase import create_client
from direct_supabase_query import get_session_route_points, initialize_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_location_points_for_session(session_id):
    """
    Get location points for a specific session ID.
    Returns the points as a list sorted by timestamp.
    """
    try:
        # Cast session_id to integer to ensure proper query
        if isinstance(session_id, str):
            session_id = int(session_id)
            
        # Get points using the existing function
        points = get_session_route_points(session_id)
        
        if not points or len(points) == 0:
            logger.warning(f"No location points found for session {session_id}")
            return []
        
        logger.info(f"Found {len(points)} location points for session {session_id}")
        return points
    except Exception as e:
        logger.error(f"Error getting location points: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def query_location_points_directly(session_id):
    """
    Query the location_point table directly with Supabase client.
    This is an alternative method to get the data.
    """
    try:
        # Initialize Supabase client
        client = initialize_supabase_client()
        
        # Query location_point table for this session
        response = client.table('location_point').select('*').eq('session_id', session_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"No location points found for session {session_id} using direct query")
            return []
        
        logger.info(f"Found {len(response.data)} location points using direct query")
        return response.data
    except Exception as e:
        logger.error(f"Error with direct location query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def get_available_session_ids_with_locations():
    """
    Get a list of session IDs that have location data.
    """
    try:
        # Initialize Supabase client
        client = initialize_supabase_client()
        
        # Query for distinct session IDs that have location points
        response = client.table('location_point').select('session_id').execute()
        
        if not response.data:
            logger.warning("No sessions with location data found")
            return []
        
        # Extract unique session IDs
        session_ids = set()
        for record in response.data:
            session_ids.add(record['session_id'])
        
        logger.info(f"Found {len(session_ids)} sessions with location data")
        return list(session_ids)
    except Exception as e:
        logger.error(f"Error getting sessions with location data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def format_location_point(point):
    """Format a location point for display."""
    return {
        'id': point.get('id'),
        'latitude': point.get('latitude'),
        'longitude': point.get('longitude'),
        'altitude': point.get('altitude'),
        'timestamp': point.get('timestamp'),
        'created_at': point.get('created_at')
    }

def main():
    """Main function to retrieve and display location data."""
    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]
        else:
            command = "help"  # Default to help
        
        # Handle different commands
        if command == "list":
            # List all sessions with location data
            session_ids = get_available_session_ids_with_locations()
            
            print("\n=== Sessions with Location Data ===")
            if session_ids:
                for session_id in sorted(session_ids):
                    print(f"Session ID: {session_id}")
            else:
                print("No sessions with location data found.")
            print("===================================\n")
            
        elif command == "session" and len(sys.argv) > 2:
            # Get data for a specific session
            session_id = sys.argv[2]
            points = get_location_points_for_session(session_id)
            
            print(f"\n=== Location Points for Session {session_id} ===")
            if points:
                print(f"Total points: {len(points)}")
                
                # Display first point
                if len(points) > 0:
                    first_point = format_location_point(points[0])
                    print("\nFirst point:")
                    for key, value in first_point.items():
                        print(f"  {key}: {value}")
                
                # Display last point
                if len(points) > 1:
                    last_point = format_location_point(points[-1])
                    print("\nLast point:")
                    for key, value in last_point.items():
                        print(f"  {key}: {value}")
                
                # Option to save all points to a file
                if len(sys.argv) > 3 and sys.argv[3] == "save":
                    filename = f"session_{session_id}_location_points.json"
                    with open(filename, 'w') as f:
                        json.dump(points, f, indent=2)
                    print(f"\nSaved all {len(points)} points to {filename}")
            else:
                # If first method failed, try direct query
                print("No points found with first method, trying direct query...")
                direct_points = query_location_points_directly(session_id)
                
                if direct_points:
                    print(f"Found {len(direct_points)} points using direct query!")
                    
                    # Display first point
                    if len(direct_points) > 0:
                        first_point = format_location_point(direct_points[0])
                        print("\nFirst point:")
                        for key, value in first_point.items():
                            print(f"  {key}: {value}")
                    
                    # Option to save all points to a file
                    if len(sys.argv) > 3 and sys.argv[3] == "save":
                        filename = f"session_{session_id}_location_points.json"
                        with open(filename, 'w') as f:
                            json.dump(direct_points, f, indent=2)
                        print(f"\nSaved all {len(direct_points)} points to {filename}")
                else:
                    print("No location points found for this session with either method.")
            print("=====================================\n")
            
        elif command == "recent":
            # Get data for the most recent session with location points
            try:
                client = initialize_supabase_client()
                response = client.table('location_point').select('session_id').order('created_at', desc=True).limit(1).execute()
                
                if response.data and len(response.data) > 0:
                    recent_session_id = response.data[0]['session_id']
                    print(f"\nMost recent session with location data: {recent_session_id}")
                    print(f"To see details, run: python read_location_data.py session {recent_session_id}")
                else:
                    print("\nNo recent sessions with location data found.")
            except Exception as e:
                logger.error(f"Error finding recent session: {e}")
                print("\nError finding recent session with location data.")
            
        else:
            # Help menu
            print("\nUsage:")
            print("  python read_location_data.py [command] [arguments]")
            print("\nCommands:")
            print("  list                    : List all sessions with location data")
            print("  session <id> [save]     : View location points for a specific session (add 'save' to save to file)")
            print("  recent                  : Find the most recent session with location data")
            print("  help                    : Show this help menu")
            print("\nExamples:")
            print("  python read_location_data.py list")
            print("  python read_location_data.py session 643")
            print("  python read_location_data.py session 643 save")
            print("  python read_location_data.py recent")
            
        return True
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 