#!/usr/bin/env python
# post_ruck_session.py - Script to post a ruck session to X (Twitter)

import logging
import os
import sys
from datetime import datetime
import api_client
import content_generator
from supabase_client import initialize_supabase_client, get_session_with_map, format_session_data, get_location_from_session, get_session_route_points, generate_map_image
from direct_supabase_query import get_session_by_id, get_recent_sessions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Post a ruck session to X (Twitter)."""
    try:
        # Check if we're in dry run mode
        dry_run = False
        if "--dryrun" in sys.argv or "--dry-run" in sys.argv:
            dry_run = True
            logger.info("DRY RUN MODE - No tweets will be posted")
            # Remove the dry run flag from argv so we can still get the session ID if provided
            if "--dryrun" in sys.argv:
                sys.argv.remove("--dryrun")
            if "--dry-run" in sys.argv:
                sys.argv.remove("--dry-run")
        
        # Check for required environment variables (skip in dry run mode)
        if not dry_run:
            required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 
                            'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
                return False
        
        # Initialize API clients
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        if not dry_run:
            logger.info("Initializing X client...")
            x_client = api_client.initialize_x_client(max_retries=3, retry_delay=5, verify=False)
        
        # Get session ID from command line if provided
        session_id = None
        if len(sys.argv) > 1:
            session_id = sys.argv[1]
            logger.info(f"Using provided session ID: {session_id}")
        
        # Fetch session data
        session_data = None
        if session_id:
            # First try the standard API approach
            response = supabase_client.table('ruck_session').select('*').eq('id', session_id).execute()
            if response.data:
                session_data = response.data[0]
                logger.info(f"Found session {session_id} using standard API")
            else:
                # If standard API fails, try direct SQL query
                logger.info(f"Session {session_id} not found via standard API, trying direct SQL query...")
                session_data = get_session_by_id(session_id)
                if session_data:
                    logger.info(f"Found session {session_id} using direct SQL query")
                else:
                    logger.error(f"No session found with ID {session_id} using either method")
                    return False
        else:
            # Get most recent session that's longer than 5 minutes (300 seconds)
            logger.info("Looking for rucks longer than 5 minutes...")
            # First try standard API
            response = supabase_client.table('ruck_session')\
                    .select('*')\
                    .gt('duration_seconds', 300)\
                    .order('started_at', desc=True)\
                    .limit(1)\
                    .execute()
            
            if response.data:
                session_data = response.data[0]
                session_id = session_data['id']
                logger.info(f"Found session {session_id} using standard API")
            else:
                # Try direct SQL query if standard API returns no results
                logger.info("No results from standard API, trying direct SQL query...")
                recent_sessions = get_recent_sessions(limit=1, min_duration=300)
                if recent_sessions:
                    session_data = recent_sessions[0]
                    session_id = session_data['id']
                    logger.info(f"Found session {session_id} using direct SQL query")
                else:
                    logger.error("No ruck sessions found that are longer than 5 minutes using either method")
                    return False
            
            logger.info(f"Using session ID: {session_id} with duration {session_data.get('duration_seconds')} seconds")
        
        # Double-check that the session is at least 5 minutes long
        duration_seconds = session_data.get('duration_seconds', 0)
        if duration_seconds < 300:
            logger.warning(f"Ruck session {session_id} is only {duration_seconds} seconds (less than 5 minutes)")
            if not session_id:  # If we weren't explicitly asked to post this session
                logger.error("Skipping post because ruck is too short")
                return False
            # Only continue if a specific session ID was requested
            
        # Format session data for display
        formatted_data = format_session_data(session_data)
        logger.info(f"Formatted session data: {formatted_data}")
        
        # Get location information for the session
        try:
            location_data = get_location_from_session(supabase_client, session_id)
            logger.info(f"Location data: {location_data}")
            
            # Add location information to formatted data
            formatted_data['city'] = location_data.get('city', '')
            formatted_data['state'] = location_data.get('state', '')
            formatted_data['country'] = location_data.get('country', '')
            
            if location_data.get('city'):
                logger.info(f"Added location: {location_data.get('city')}, {location_data.get('state')}, {location_data.get('country')}")
            else:
                logger.warning("No location data found for this session")
        except Exception as loc_error:
            logger.error(f"Error getting location data: {loc_error}")
        
        # Generate a map image for the session
        map_path = None
        try:
            logger.info(f"Generating map for session {session_id}...")
            
            # Get route points
            route_points = get_session_route_points(supabase_client, session_id)
            if route_points and len(route_points) >= 2:
                logger.info(f"Found {len(route_points)} route points for map generation")
                # Generate map image
                map_path = generate_map_image(route_points, formatted_data)
                if map_path:
                    logger.info(f"Generated map image: {map_path}")
                else:
                    logger.warning("Failed to generate map image")
            else:
                logger.warning(f"Not enough route points to generate map (need at least 2, found {len(route_points) if route_points else 0})")
        except Exception as map_error:
            logger.error(f"Error generating map: {map_error}")
            
        # Generate post text
        post_text = content_generator.generate_map_post_text(formatted_data)
        
        # Ensure it's within character limit
        if len(post_text) > 280:
            post_text = post_text[:276] + " ..."
        
        # Post tweet 
        logger.info(f"Tweet content: {post_text}")
        logger.info(f"Tweet length: {len(post_text)} characters")
        
        # In dry run mode, just show the tweet content
        if dry_run:
            print("\n" + "="*80)
            print("DRY RUN - TWEET PREVIEW:")
            print("="*80)
            print(post_text)
            print("="*80 + "\n")
            logger.info("Dry run complete - tweet NOT posted")
            return True
        
        # Confirm with user
        print("\n" + "="*80)
        print("TWEET PREVIEW:")
        print("="*80)
        print(post_text)
        print("="*80 + "\n")
        
        confirm = input("Post this tweet? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("Tweet canceled by user")
            return False
        
        # Post the tweet
        if map_path and os.path.exists(map_path):
            logger.info(f"Posting tweet with map image: {map_path}")
            tweet_id = api_client.post_tweet(x_client, post_text, media=map_path)
        else:
            logger.info("Posting tweet without map image")
            tweet_id = api_client.post_tweet(x_client, post_text)
            
        logger.info(f"Successfully posted tweet with ID: {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error posting ruck session: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    print(f"Ruck session post {'succeeded' if success else 'failed'}") 