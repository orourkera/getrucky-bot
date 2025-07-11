# main.py

import logging
import sys
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import api_client
import scheduler
import backup
from flask import Flask, jsonify
from config import get_config, validate_config, get_post_times
import threading
import traceback

# Configure logging for Heroku Logplex
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables for sharing state
x_client = None
readonly_client = None

def initialize_clients():
    """Initialize API clients with proper error handling and retries."""
    global x_client, readonly_client
    try:
        logger.info("Initializing API clients")
        x_client = api_client.initialize_x_client(max_retries=5, retry_delay=10, verify=False)
        readonly_client = api_client.initialize_readonly_client()
        logger.info("API clients initialized successfully")
        return x_client
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """Main function to initialize and run the AI Marketing Bot (full mode with engagement)."""
    global x_client, readonly_client
    logger.info("Starting AI Marketing Bot for @getrucky (full mode with engagement)")

    # Log all available environment variables for the worker dyno
    logger.info("---Dumping All Environment Variables (Worker Dyno) ---")
    for key, value in os.environ.items():
        # For potentially sensitive keys, log only partial info or just their presence
        if "KEY" in key.upper() or "SECRET" in key.upper() or "TOKEN" in key.upper():
            logger.info(f"ENV: {key}=<present - length {len(value)}> - First 4: {value[:4] if len(value) > 0 else ''}")
        else:
            logger.info(f"ENV: {key}={value}")
    logger.info("--- End of Environment Variables Dump ---")
    
    # Validate configuration
    logger.info("Validating configuration")
    config_status = validate_config()
    
    essential_keys_present = all([
        config_status.get('X_API_KEY', False),
        config_status.get('X_API_SECRET', False),
        config_status.get('X_ACCESS_TOKEN', False),
        config_status.get('X_ACCESS_TOKEN_SECRET', False),
        config_status.get('AI_API_KEY', False) 
    ])

    if not essential_keys_present:
        logger.error("CRITICAL environment variables missing. Worker process will exit. Check logs from validate_config for details.")
        sys.exit(1)
    elif not all(config_status.values()): 
        logger.warning("Some non-critical environment variables might be missing (e.g., for map functionality). Bot will attempt to continue. Check logs from validate_config.")
    else:
        logger.info("Configuration validated successfully")
    
    # Initialize databases
    logger.info("Initializing databases")
    success = backup.initialize_databases()
    if not success:
        logger.warning("Database initialization had issues, will attempt to continue")
    
    # Initialize API clients
    x_client = initialize_clients()
    
    # If DATABASE_URL is set, try to restore databases from Postgres
    if os.getenv('DATABASE_URL'):
        logger.info("Attempting to restore databases from Heroku Postgres")
        for db_name in ['pun_library', 'interaction_log', 'analytics', 'model_cache']:
            try:
                backup.restore_db(db_name)
            except Exception as e:
                logger.warning(f"Failed to restore {db_name}: {e}")
    
    # Initialize scheduler for full mode with engagement
    logger.info("Initializing scheduler (full mode with engagement)")
    scheduler_instance = BackgroundScheduler()
    
    # Schedule content posts for the day
    post_times = get_post_times()
    logger.info(f"Selected {len(post_times)} post times for today")
    scheduler.schedule_posts(scheduler_instance, x_client, None, api_client.initialize_ai_client())
    
    logger.info("Scheduling engagement tasks with rate limiting")
    
    def safe_engagement():
        try:
            rate_limits = api_client.check_rate_limit_status()
            
            if rate_limits:
                safe_to_proceed = True
                for category, endpoints in rate_limits.items():
                    for endpoint, limits in endpoints.items():
                        if limits.get('remaining', 100) < 20:
                            logger.warning(f"Rate limit buffer reached for {endpoint}. Skipping engagement.")
                            safe_to_proceed = False
                            break
                    if not safe_to_proceed: # break outer loop if already decided not to proceed
                        break 
                
                if not safe_to_proceed:
                    logger.info("Engagement deferred due to rate limit concerns.")
                    return
            
            ai_headers = api_client.initialize_ai_client()
            result = scheduler.engage_with_posts(readonly_client or x_client, ai_headers)
            logger.info(f"Engagement completed: {result}")
        except Exception as e:
            logger.error(f"Error in safe engagement: {e}")
    
    scheduler_instance.add_job(
        safe_engagement,
        IntervalTrigger(hours=8),
        id='engagement_task_8h'
    )
    
    scheduler_instance.add_job(
        backup.backup_db,
        CronTrigger(hour=2, minute=0),
        id='database_backup'
    )
    
    scheduler_instance.start()
    logger.info("Scheduler started successfully (full mode with engagement)")
    
    while True:
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    global x_client
    try:
        if not x_client:
            return jsonify({
                'status': 'error',
                'message': 'X API client not initialized'
            }), 500
        return jsonify({'status': 'ok', 'message': 'Full mode with engagement'})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    main() 