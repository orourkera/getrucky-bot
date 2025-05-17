#!/usr/bin/env python
# check_session_id_range.py - Script to check which session IDs are accessible via the Supabase API

import logging
import os
import sys
from supabase_client import initialize_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_id_range(start_id, end_id, step=1):
    """Check which session IDs in the given range are accessible via the Supabase API."""
    try:
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase_client = initialize_supabase_client()
        
        logger.info(f"Checking session IDs from {start_id} to {end_id} (step {step})...")
        
        # Store results
        found_ids = []
        missing_ids = []
        
        # Check each ID in the range
        for session_id in range(start_id, end_id + 1, step):
            response = supabase_client.table('ruck_session').select('id, created_at, started_at, duration_seconds').eq('id', session_id).execute()
            
            if response.data:
                session_data = response.data[0]
                found_ids.append((session_id, session_data))
                logger.info(f"Found session ID {session_id}: created_at={session_data.get('created_at')}, duration={session_data.get('duration_seconds')}s")
            else:
                missing_ids.append(session_id)
                logger.info(f"No session found with ID {session_id}")
        
        # Print summary
        logger.info(f"\nSUMMARY:")
        logger.info(f"Found {len(found_ids)} sessions, missing {len(missing_ids)} sessions")
        
        if found_ids:
            logger.info("\nFound session IDs:")
            for session_id, data in found_ids:
                logger.info(f"ID {session_id}: created_at={data.get('created_at')}, duration={data.get('duration_seconds')}s")
        
        if missing_ids:
            logger.info("\nMissing session IDs:")
            # Display in ranges for readability
            current_range_start = missing_ids[0]
            current_range_end = missing_ids[0]
            
            for i in range(1, len(missing_ids)):
                if missing_ids[i] == current_range_end + step:
                    current_range_end = missing_ids[i]
                else:
                    if current_range_start == current_range_end:
                        logger.info(f"ID {current_range_start}")
                    else:
                        logger.info(f"IDs {current_range_start}-{current_range_end}")
                    current_range_start = missing_ids[i]
                    current_range_end = missing_ids[i]
            
            # Print the last range
            if current_range_start == current_range_end:
                logger.info(f"ID {current_range_start}")
            else:
                logger.info(f"IDs {current_range_start}-{current_range_end}")
        
        # Check specifically for ID 684 which was mentioned as problematic
        if 684 >= start_id and 684 <= end_id:
            logger.info("\nSpecific check for session ID 684:")
            response = supabase_client.table('ruck_session').select('*').eq('id', 684).execute()
            if response.data:
                logger.info(f"Session ID 684 EXISTS and has fields: {list(response.data[0].keys())}")
                logger.info(f"Duration: {response.data[0].get('duration_seconds')} seconds")
            else:
                logger.info("Session ID 684 does NOT exist in the database")
        
        return True
    except Exception as e:
        logger.error(f"Error checking session ID range: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to run the session ID range check."""
    # Check if we have start and end IDs from command line
    if len(sys.argv) >= 3:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])
        
        # Optional step parameter
        step = 1
        if len(sys.argv) >= 4:
            step = int(sys.argv[3])
    else:
        # Default: check IDs 640-690, which should include problematic ID 684
        start_id = 640
        end_id = 690
        step = 1
        
        print("\nNo ID range specified. Using default range 640-690.")
        print("Usage: python check_session_id_range.py <start_id> <end_id> [step]")
        print("Example: python check_session_id_range.py 640 690 1\n")
    
    success = check_id_range(start_id, end_id, step)
    print(f"\nSession ID range check {'succeeded' if success else 'failed'}")

if __name__ == "__main__":
    main() 