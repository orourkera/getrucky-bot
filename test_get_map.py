#!/usr/bin/env python
# test_get_map.py - Script to test generating a map

import logging
import os
from datetime import datetime
import tempfile
from supabase_client import initialize_supabase_client, get_session_with_map
from supabase_client import get_recent_ruck_sessions, get_session_route_points

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test generating a map for a session."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        # Get the most recent sessions
        logger.info("Fetching recent ruck sessions...")
        sessions = get_recent_ruck_sessions(supabase_client, limit=10)
        
        if not sessions:
            logger.error("No ruck sessions found")
            return False
        
        logger.info(f"Found {len(sessions)} sessions")
        
        # Try to get location points for each session
        for session in sessions:
            session_id = session['id']
            logger.info(f"Checking for location points for session ID: {session_id}")
            
            try:
                # First try the direct location_point query
                points = get_session_route_points(supabase_client, session_id)
                
                if points:
                    logger.info(f"Found {len(points)} location points for session {session_id}")
                    
                    # If no location points found, we'll add some dummy data for testing
                    if len(points) < 2:
                        logger.warning(f"Not enough real location points for session {session_id}, using dummy data")
                        
                        # Central Park, NYC dummy route
                        dummy_points = [
                            (40.767, -73.9761),
                            (40.7702, -73.9745),
                            (40.7736, -73.9732),
                            (40.7764, -73.9719),
                            (40.7804, -73.9684),
                            (40.7829, -73.9652),
                            (40.7818, -73.9625),
                            (40.7777, -73.9647),
                            (40.7741, -73.9677),
                            (40.7705, -73.9710),
                            (40.767, -73.9761)
                        ]
                        
                        # Use real starter points if we had at least one
                        if len(points) == 1:
                            start_point = points[0]
                            # Calculate relative offsets from the real starting point
                            real_lat, real_lng = start_point
                            dummy_points = [(real_lat + (p[0] - dummy_points[0][0]), 
                                            real_lng + (p[1] - dummy_points[0][1])) 
                                           for p in dummy_points]
                        
                        # Generate a test map with these points
                        import folium
                        
                        # Calculate center point
                        center_lat = sum(p[0] for p in dummy_points) / len(dummy_points)
                        center_lng = sum(p[1] for p in dummy_points) / len(dummy_points)
                        
                        # Create a map centered at the middle of the route
                        m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
                        
                        # Add the route line
                        folium.PolyLine(
                            dummy_points,
                            color='blue',
                            weight=5,
                            opacity=0.8
                        ).add_to(m)
                        
                        # Add markers
                        folium.Marker(
                            location=dummy_points[0],
                            icon=folium.Icon(color='green', icon='play'),
                            popup='Start'
                        ).add_to(m)
                        
                        folium.Marker(
                            location=dummy_points[-1],
                            icon=folium.Icon(color='red', icon='stop'),
                            popup='End'
                        ).add_to(m)
                        
                        # Save map to a temp file
                        temp_dir = tempfile.mkdtemp()
                        html_file = f"{temp_dir}/test_map_{session_id}.html"
                        m.save(html_file)
                        
                        logger.info(f"Generated test map saved to: {html_file}")
                        logger.info(f"Open this file in a browser to view the map")
                        
                        return True
                    else:
                        logger.info(f"Using {len(points)} real location points to generate map")
                        # Similar to above code but using real points
                        import folium
                        
                        # Calculate center point
                        center_lat = sum(p[0] for p in points) / len(points)
                        center_lng = sum(p[1] for p in points) / len(points)
                        
                        # Create a map centered at the middle of the route
                        m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
                        
                        # Add the route line
                        folium.PolyLine(
                            points,
                            color='blue',
                            weight=5,
                            opacity=0.8
                        ).add_to(m)
                        
                        # Add markers
                        folium.Marker(
                            location=points[0],
                            icon=folium.Icon(color='green', icon='play'),
                            popup='Start'
                        ).add_to(m)
                        
                        folium.Marker(
                            location=points[-1],
                            icon=folium.Icon(color='red', icon='stop'),
                            popup='End'
                        ).add_to(m)
                        
                        # Save map to a temp file
                        temp_dir = tempfile.mkdtemp()
                        html_file = f"{temp_dir}/real_map_{session_id}.html"
                        m.save(html_file)
                        
                        logger.info(f"Generated real map saved to: {html_file}")
                        logger.info(f"Open this file in a browser to view the map")
                        
                        return True
            except Exception as e:
                logger.error(f"Error processing session {session_id}: {e}")
                continue
        
        logger.warning("Could not generate a map for any session")
        return False
    except Exception as e:
        logger.error(f"Error testing map generation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Map generation test {'succeeded' if success else 'failed'}") 