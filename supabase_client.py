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
    """Fetch route points for a specific ruck session using a join between tables."""
    try:
        logger.info(f"Fetching route points for session {session_id}")
        
        # Convert session_id to integer
        int_session_id = int(session_id)
        
        # First get the session to ensure it exists and to get any foreign key references
        logger.info(f"Getting session details for session_id = {int_session_id}")
        session_response = client.table('ruck_session').select('*').eq('id', int_session_id).execute()
        
        if not session_response.data:
            logger.warning(f"Session {int_session_id} not found")
            return []
        
        session = session_response.data[0]
        logger.info(f"Found session: {session}")
        
        # Check if we have a user_id that might be needed for the join
        user_id = session.get('user_id')
        
        # Try different approaches to find location points
        
        # Direct query first
        logger.info(f"Querying location_point with session_id = {int_session_id}")
        response = client.table('location_point').select('*').eq('session_id', int_session_id).execute()
        
        # If that doesn't work, try using the user_id if available
        if not response.data and user_id:
            logger.info(f"Trying to find location points for user_id = {user_id}")
            # This assumes location points might be linked to user_id rather than session_id
            try:
                response = client.table('location_point').select('*').eq('user_id', user_id).execute()
            except Exception as e:
                logger.warning(f"Error querying by user_id: {e}")
        
        # Try to find location points that were created around the same time as the session
        if not response.data and 'started_at' in session and 'completed_at' in session:
            started_at = session.get('started_at')
            completed_at = session.get('completed_at')
            
            if started_at and completed_at:
                logger.info(f"Trying to find location points created between {started_at} and {completed_at}")
                try:
                    # Only try this if the location_point table has a timestamp field
                    response = client.table('location_point').select('*').gte('timestamp', started_at).lte('timestamp', completed_at).execute()
                except Exception as e:
                    logger.warning(f"Error querying by timestamp: {e}")
        
        # Process results
        if response.data and len(response.data) >= 2:
            # Extract latitude and longitude from each point
            route_points = [(point['latitude'], point['longitude']) for point in response.data]
            logger.info(f"Fetched {len(route_points)} route points for session {session_id}")
            return route_points
        
        # No route points found
        logger.warning(f"No route points found for session {session_id}")
        return []
    except ValueError:
        logger.error(f"Failed to convert session_id '{session_id}' to integer")
        return []
    except Exception as e:
        logger.error(f"Error fetching route points for session {session_id}: {e}")
        return []

def geocode_coordinates(latitude: float, longitude: float) -> Dict[str, str]:
    """Geocode coordinates to get city, state, country, and potentially a specific feature name."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1"
        headers = {
            "User-Agent": "GetruckyBot/1.0",
            "Accept-Language": "en-US,en"
        }
        response = requests.get(url, headers=headers, timeout=10) # Increased timeout slightly
        response.raise_for_status()
        result = response.json()
        address = result.get('address', {})

        feature_name = ""
        # Prioritize specific, significant features. Order matters.
        poi_priority = [
            'national_park', 'park', 'forest', 'nature_reserve', 'conservation', 
            'state_park', 'mountain_range', 'peak', 'island', 'beach', 'historic', 'archaeological_site'
            # 'tourism' and 'leisure' can be too broad or might be shops/restaurants
        ]
        for key in poi_priority:
            if address.get(key):
                feature_name = address.get(key)
                break
        
        # Get standard administrative areas
        city = address.get('city', address.get('town', address.get('village', address.get('hamlet', ''))))
        county = address.get('county', '') # Often useful if city is small or not present
        state = address.get('state', '')
        country = address.get('country', '')

        # If no specific feature, but we have a suburb/neighbourhood, that can be useful detail
        if not feature_name and not city: # Only if city is also missing
            sub_feature = address.get('suburb', address.get('neighbourhood', ''))
            if sub_feature:
                feature_name = sub_feature # Use it as a less specific feature

        logger.info(f"Geocoded ({latitude}, {longitude}): Feature='{feature_name}', City='{city}', County='{county}', State='{state}', Country='{country}'")
        
        return {
            'feature': feature_name or "",
            'city': city or "",
            'county': county or "",
            'state': state or "",
            'country': country or ""
        }
    except Exception as e:
        logger.error(f"Error geocoding coordinates: {e} (URL: {url if 'url' in locals() else 'not set'})")
        return {
            'feature': "", 'city': "", 'county': "", 'state': "", 'country': ""
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
        # Get the route points using our improved join-based function
        logger.info(f"Getting location from route points for session {session_id}")
        route_points = get_session_route_points(client, session_id)
        
        # Check if we got any route points
        if route_points and len(route_points) > 0:
            # Use the first point for geocoding
            latitude, longitude = route_points[0]
            logger.info(f"Using location point: lat={latitude}, lon={longitude}")
            
            # Geocode the coordinates
            location = geocode_coordinates(latitude, longitude)
            return location
        
        # If no points found, return empty values
        logger.warning(f"No route points found for session {session_id}")
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
    
    # Define these variables from session_data at the beginning for use in filename and potentially other logic
    distance = session_data.get('distance', '0') 
    username = session_data.get('user', 'user')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    try:
        # Calculate center point for the map
        center_lat = sum(point[0] for point in route_points) / len(route_points)
        center_lng = sum(point[1] for point in route_points) / len(route_points)
        
        # Create a map centered at the middle of the route with Stamen Terrain tiles
        m = folium.Map(
            location=[center_lat, center_lng], 
            zoom_start=14,
            tiles='Stamen Terrain',
            attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors'
        )
        
        # Add custom route line with the new color
        folium.PolyLine(
            route_points,
            color='#CC6A2A',  # Brownish-orange
            weight=5,        
            opacity=0.85, # Slightly more opaque for better visibility on varied terrain
            dash_array=None 
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
        
        # Add a title and branding to the map
        title_html = f"""
        <div style="
            position: absolute; 
            top: 10px; 
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background-color: rgba(255, 255, 255, 0.85); /* Match stats box background */
            color: #2F2F2F; /* Match stats box text color */
            padding: 8px 15px;
            border-radius: 20px;
            font-family: Arial, sans-serif;
            font-size: 15px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        ">
            <b>@getrucky</b> | Ruck Session Map
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Fit the map to the route bounds with some padding
        m.fit_bounds(route_points, padding=(30, 30))
        
        # Create a unique filename with timestamp
        # timestamp = datetime.now().strftime('%Y%m%d%H%M%S') # Already defined above
        # username = session_data.get('user', 'user') # Already defined above
        
        # Save map to a temp file
        temp_dir = tempfile.mkdtemp()
        html_file = f"{temp_dir}/ruck_map_{username}_{distance}_{timestamp}.html"
        
        # Save the map as HTML
        m.save(html_file)
        
        # Convert HTML to PNG image using Selenium
        try:
            # Check if we're on Heroku (which has Chrome driver installed)
            if 'DYNO' in os.environ:
                import selenium
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                import time
                
                logger.info("Using Chrome headless browser to convert HTML to PNG")
                
                # Set up headless Chrome browser options
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                # Add a unique user data directory to prevent conflicts
                user_data_dir = os.path.join(tempfile.gettempdir(), f"chrome_user_data_{timestamp}")
                os.makedirs(user_data_dir, exist_ok=True)
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
                
                # Set browser window size for the image
                chrome_options.add_argument("--window-size=1200,800")
                
                # Create a Chrome WebDriver instance with these options
                driver = webdriver.Chrome(options=chrome_options)
                
                # Open the HTML file
                html_path = f"file://{html_file}"
                logger.info(f"Opening HTML file: {html_path}")
                driver.get(html_path)
                
                # Wait for map to fully load - increased sleep time
                logger.info("Waiting for map tiles to load...")
                time.sleep(7) # Increased from 2 to 7 seconds
                
                # Create PNG file path
                png_file = html_file.replace('.html', '.png')
                
                # Take a screenshot and save as PNG
                driver.save_screenshot(png_file)
                driver.quit()
                
                logger.info(f"Saved map as PNG: {png_file}")
                return png_file
            else:
                # We're not on Heroku, just return the HTML
                logger.info(f"Generated enhanced map HTML for {username}'s ruck session ({distance} miles): {html_file}")
                return html_file
        except Exception as screenshot_error:
            # If screenshot fails, fall back to returning the HTML
            logger.error(f"Error converting map to PNG: {screenshot_error}")
            logger.info(f"Falling back to HTML map: {html_file}")
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