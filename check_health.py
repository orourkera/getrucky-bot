#!/usr/bin/env python
# check_health.py - Script to manually check health status of all components

import logging
import json
import sys
from health import check_database_health, check_system_health, get_health_status

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run a manual health check and print detailed results."""
    logger.info("Starting manual health check...")
    
    # Check database health
    logger.info("Checking database health...")
    db_health = check_database_health()
    print("\nDATABASE HEALTH:")
    for db_name, status in db_health.items():
        print(f"- {db_name}: {status['status']}")
        # Print additional details if available
        for key, value in status.items():
            if key != 'status':
                print(f"  • {key}: {value}")
                
    # Check system health
    logger.info("Checking system health...")
    sys_health = check_system_health()
    print("\nSYSTEM HEALTH:")
    try:
        # Memory
        print(f"- Memory: {sys_health['memory']['percent_used']}% used")
        print(f"  • Available: {sys_health['memory']['available'] / (1024*1024):.2f} MB")
        
        # Disk
        print(f"- Disk: {sys_health['disk']['percent_used']}% used")
        print(f"  • Free: {sys_health['disk']['free'] / (1024*1024*1024):.2f} GB")
        
        # Environment
        print("- Environment:")
        for key, value in sys_health['environment'].items():
            print(f"  • {key}: {value}")
    except (KeyError, TypeError):
        print(f"  System health error: {sys_health}")
    
    # Print SQLite DB paths
    print("\nDATABASE PATHS:")
    from config import SQLITE_DB_PATH
    print(f"- SQLite DB Path: {SQLITE_DB_PATH}")
    
    # Check database files existence
    import os
    print("\nDATABASE FILES EXISTENCE:")
    db_files = {
        'pun_library': f"{SQLITE_DB_PATH}/pun_library.db",
        'interaction_log': f"{SQLITE_DB_PATH}/interaction_log.db",
        'analytics': f"{SQLITE_DB_PATH}/analytics.db",
        'model_cache': f"{SQLITE_DB_PATH}/model_cache.db"
    }
    for db_name, db_path in db_files.items():
        exists = os.path.exists(db_path)
        size = os.path.getsize(db_path) if exists else 0
        print(f"- {db_name}: {'✅ Exists' if exists else '❌ Missing'} (Size: {size} bytes)")
    
    logger.info("Manual health check completed.")

if __name__ == "__main__":
    main() 