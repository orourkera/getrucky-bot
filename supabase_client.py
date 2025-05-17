# supabase_client.py

import os
import logging
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import io
import polyline
import requests
from PIL import Image
from supabase import create_client, Client
import folium
from folium.plugins import HeatMap

logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
STADIA_API_KEY = os.getenv('STADIA_API_KEY', '')

def initialize_supabase_client() -> Client:
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

def get_recent_ruck_sessions(client: Client, limit: int = 5) -> List[Dict[Any, Any]]:
    """Fetch recent ruck sessions from Supabase."""
    try:
        response = client.table('ruck_session').select('*').order('started_at', desc=True).limit(limit).execute()
        
        if not response.data:
            logger.warning(f"No ruck sessions found in Supabase")
            return []
        
        logger.info(f"Fetched {len(response.data)} ruck sessions from Supabase")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching ruck sessions from Supabase: {e}")
        return []

def get_session_route_points(client: Client, session_id: str) -> List[Tuple[float, float]]:
    """Fetch route points for a specific ruck session or generate dummy points if none exist."""
    try:
        # Query the location_point table with proper integer session_id
        logger.info(f"Fetching route points for session {session_id}")
        
        # Convert session_id to integer for database query since it's an integer column
        int_session_id = int(session_id)
        logger.info(f"Querying location_point with session_id = {int_session_id}")    
        response = client.table('location_point').select('*').eq('session_id', int_session_id).execute()
        
        logger.info(f"Query response data count: {len(response.data) if response.data else 0}")
        
        if response.data and len(response.data) >= 2:
            # Extract latitude and longitude from each point
            route_points = [(point['latitude'], point['longitude']) for point in response.data]
            logger.info(f"Fetched {len(route_points)} real route points for session {session_id}")
            return route_points
        else:
            # No route points found, but don't generate dummy data - just return empty list
            logger.warning(f"No route points found for session {session_id}")
            return []
    except ValueError:
        logger.error(f"Failed to convert session_id '{session_id}' to integer")
        return []
    except Exception as e:
        logger.error(f"Error fetching route points for session {session_id}: {e}")
        return []

def geocode_coordinates(latitude: float, longitude: float) -> Dict[str, str]:
    """Geocode coordinates to get city, state, country using a free geocoding API.
    
    Args:
        latitude: The latitude coordinate
        longitude: The longitude coordinate
        
    Returns:
        A dictionary with keys 'city', 'state', and 'country'
    """
    try:
        # Use the free OpenStreetMap Nominatim API for geocoding
        # Rate limit is 1 request per second, which is fine for our use case
        url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"
        
        headers = {
            "User-Agent": "GetruckyBot/1.0",  # Nominatim requires a User-Agent
            "Accept-Language": "en-US,en"  # Get English names
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract location components
        address = result.get('address', {})
        city = address.get('city', address.get('town', address.get('village', address.get('hamlet', ''))))
        state = address.get('state', '')
        country = address.get('country', '')
        
        logger.info(f"Geocoded coordinates ({latitude}, {longitude}) to {city}, {state}, {country}")
        
        return {
            'city': city or "",
            'state': state or "",
            'country': country or ""
        }
    except Exception as e:
        logger.error(f"Error geocoding coordinates: {e}")
        return {
            'city': "",
            'state': "",
            'country': ""
        }

def get_location_from_session(client: Client, session_id: str) -> Dict[str, str]:
    """Get the location (city, state, country) for a ruck session using the first route point.
    
    Args:
        client: The Supabase client
        session_id: The session ID to get location for
        
    Returns:
        A dictionary with keys 'city', 'state', and 'country'
    """
    try:
        # Query the location_point table for this session with proper integer conversion
        logger.info(f"Querying location points for session {session_id}")
        
        # Convert session_id to integer
        int_session_id = int(session_id)
        
        # Get the first location point
        response = client.table('location_point').select('latitude,longitude').eq('session_id', int_session_id).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            # Get the first point
            first_point = response.data[0]
            latitude = first_point.get('latitude')
            longitude = first_point.get('longitude')
            
            logger.info(f"Found location point: lat={latitude}, lon={longitude}")
            
            # Geocode the coordinates
            location = geocode_coordinates(latitude, longitude)
            return location
        
        # If no points found, return empty values
        logger.warning(f"No location points found for session {session_id}")
        return {
            'city': "",
            'state': "",
            'country': ""
        }
    except ValueError:
        logger.error(f"Failed to convert session_id '{session_id}' to integer")
        return {
            'city': "",
            'state': "",
            'country': ""
        }
    except Exception as e:
        logger.error(f"Error getting location for session {session_id}: {e}")
        return {
            'city': "",
            'state': "",
            'country': ""
        }

def generate_map_image(route_points: List[Tuple[float, float]], session_data: Dict[Any, Any]) -> Optional[str]:
    """Generate a map image from route points using Folium and return the path to the saved image."""
    if not route_points or len(route_points) < 2:
        logger.warning("Not enough route points to generate a map")
        return None
    
    try:
        # Calculate center point for the map
        center_lat = sum(point[0] for point in route_points) / len(route_points)
        center_lng = sum(point[1] for point in route_points) / len(route_points)
        
        # Create a map centered at the middle of the route with a dark theme
        m = folium.Map(
            location=[center_lat, center_lng], 
            zoom_start=14,
            tiles='CartoDB dark_matter'  # Use a dark theme for better visualization
        )
        
        # Add custom route line with a more visible style
        folium.PolyLine(
            route_points,
            color='#00FFFF',  # Cyan - highly visible on dark background
            weight=6,          # Thicker line
            opacity=0.9,
            dash_array=None    # Solid line for better visibility
        ).add_to(m)
        
        # Add nicer start marker with custom icon and popup
        start_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 150px;">
            <b>Start</b><br>
            {datetime.fromisoformat(session_data.get('started_at', datetime.now().isoformat())).strftime('%I:%M %p')}
        </div>
        """
        
        folium.Marker(
            location=route_points[0],
            icon=folium.Icon(color='green', icon='play', prefix='fa'),
            popup=folium.Popup(start_html, max_width=300)
        ).add_to(m)
        
        # Add end marker
        end_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 150px;">
            <b>Finish</b><br>
            Distance: {session_data.get('distance', '0')} miles<br>
            Duration: {session_data.get('duration', 'N/A')}
        </div>
        """
        
        folium.Marker(
            location=route_points[-1],
            icon=folium.Icon(color='red', icon='stop', prefix='fa'),
            popup=folium.Popup(end_html, max_width=300)
        ).add_to(m)
        
        # Add a heat map layer for route intensity if enough points
        if len(route_points) > 10:
            HeatMap(route_points, radius=15, blur=10, max_zoom=13).add_to(m)
        
        # Add a session stats info box with improved styling
        distance = session_data.get('distance', '0')
        duration = session_data.get('duration', '0h')
        pace = session_data.get('pace', 'N/A')
        ruck_weight = session_data.get('ruck_weight', '0')
        elevation_gain = session_data.get('elevation_gain', '0')
        
        stats_html = f"""
        <div style="
            position: absolute; 
            bottom: 30px; 
            left: 10px; 
            z-index: 1000;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: Arial;
            font-size: 14px;
            width: 220px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.5);
            border-left: 4px solid #00FFFF;
        ">
            <h4 style="margin: 0 0 10px 0; color: #00FFFF; font-size: 16px;">Ruck Stats</h4>
            <div style="margin-bottom: 5px;">🏃‍♂️ <b>Distance:</b> {distance} miles</div>
            <div style="margin-bottom: 5px;">⏱️ <b>Duration:</b> {duration}</div>
            <div style="margin-bottom: 5px;">⚡ <b>Pace:</b> {pace}/mi</div>
            <div style="margin-bottom: 5px;">🎒 <b>Weight:</b> {ruck_weight}kg</div>
            {f'<div>⛰️ <b>Elevation:</b> {elevation_gain}m</div>' if float(elevation_gain) > 0 else ''}
        </div>
        """
        
        # Add the stats HTML as a custom div
        m.get_root().html.add_child(folium.Element(stats_html))
        
        # Add a title and branding to the map
        title_html = f"""
        <div style="
            position: absolute; 
            top: 10px; 
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-family: Arial;
            font-size: 16px;
            text-align: center;
        ">
            <b>@getrucky</b> | Ruck Session Map
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Fit the map to the route bounds with some padding
        m.fit_bounds(route_points, padding=(30, 30))
        
        # Create a unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        username = session_data.get('user', 'user')
        
        # Save map to a temp file
        temp_dir = tempfile.mkdtemp()
        html_file = f"{temp_dir}/ruck_map_{username}_{distance}_{timestamp}.html"
        
        # Save the map as HTML
        m.save(html_file)
        
        logger.info(f"Generated enhanced map HTML for {username}'s ruck session ({distance} miles): {html_file}")
        return html_file
        
    except Exception as e:
        logger.error(f"Error generating map image: {e}")
        return None

def format_session_data(session_data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Format session data for display and ensure it has all required fields."""
    # Convert distance from km to miles if needed
    distance_km = session_data.get('distance_km', 0)
    if distance_km:
        distance_miles = float(distance_km) * 0.621371  # Convert km to miles
    else:
        distance_miles = 0
        
    # Format duration from seconds to hours/minutes
    duration_seconds = session_data.get('duration_seconds', 0)
    if duration_seconds:
        hours = int(duration_seconds / 3600)
        minutes = int((duration_seconds % 3600) / 60)
        if hours > 0:
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = f"{minutes}m"
    else:
        duration_str = "N/A"
    
    formatted_data = {
        'user': session_data.get('user_id', 'RuckStar'),
        'distance': f"{distance_miles:.2f}",
        'duration': duration_str,
        'total_distance': str(distance_miles),  # No total_distance in schema, using same value
        'streak': '0',  # No streak in schema
        'session_id': session_data.get('id', ''),
        'date': session_data.get('started_at', datetime.now().isoformat()),
        'ruck_weight': session_data.get('ruck_weight_kg', 0),
        'status': session_data.get('status', ''),
        'calories': session_data.get('calories_burned', 0),
        'elevation_gain': session_data.get('elevation_gain_m', 0),
        'avg_heart_rate': session_data.get('avg_heart_rate', 0),
    }
    
    # Calculate pace if available
    avg_pace = session_data.get('average_pace', None)
    if avg_pace is not None:
        # This appears to be in seconds per km, convert to min:sec per mile
        pace_seconds_per_mile = avg_pace * 1.60934  # Convert seconds/km to seconds/mile
        pace_minutes = int(pace_seconds_per_mile / 60)
        pace_seconds = int(pace_seconds_per_mile % 60)
        formatted_data['pace'] = f"{pace_minutes}:{pace_seconds:02d}"
    else:
        formatted_data['pace'] = "N/A"
    
    return formatted_data

def get_session_with_map(client: Client, session_id: Optional[str] = None) -> Tuple[Optional[Dict[Any, Any]], Optional[str]]:
    """Get a specific session or the most recent one and generate a map for it."""
    try:
        # Get session data
        if session_id:
            response = client.table('ruck_session').select('*').eq('id', session_id).execute()
            if not response.data:
                logger.warning(f"No session found with ID {session_id}")
                return None, None
            session_data = response.data[0]
        else:
            # Get most recent session that's longer than 5 minutes (300 seconds)
            response = client.table('ruck_session')\
                    .select('*')\
                    .gt('duration_seconds', 300)\
                    .order('started_at', desc=True)\
                    .limit(1)\
                    .execute()
                
            if not response.data:
                logger.warning("No sessions found that are longer than 5 minutes")
                # Try to get any session as fallback
                response = client.table('ruck_session').select('*').order('created_at', desc=True).limit(1).execute()
                if not response.data:
                    logger.warning("No sessions found at all")
                    return None, None
            
            session_data = response.data[0]
            session_id = session_data['id']
        
        # Get location information
        location = get_location_from_session(client, session_id)
        
        # Format the session data
        formatted_data = format_session_data(session_data)
        
        # Add location data to formatted_data
        formatted_data['city'] = location['city']
        formatted_data['state'] = location['state']
        formatted_data['country'] = location['country']
        
        # Get route points
        route_points = get_session_route_points(client, session_id)
        
        # Generate map image
        map_path = None
        if route_points:
            map_path = generate_map_image(route_points, formatted_data)
        
        return formatted_data, map_path
    except Exception as e:
        logger.error(f"Error getting session with map: {e}")
        return None, None 