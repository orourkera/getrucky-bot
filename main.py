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
    
    # Validate configuration
    logger.info("Validating configuration")
    config_status = validate_config()
    if not all(config_status.values()):
        logger.error("Missing required environment variables. Please check the configuration.")
        sys.exit(1)
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
    scheduler.schedule_posts(scheduler_instance, x_client, None, api_client.initialize_xai_client())
    
    # Schedule engagement tasks with rate limiting safeguards
    # Run engagement 3 times a day (every 8 hours) to avoid API rate limits
    # First run at 3 hours after startup to prioritize posting
    logger.info("Scheduling engagement tasks with rate limiting")
    
    # Create a wrapper function that implements additional rate limit safeguards
    def safe_engagement():
        try:
            # First check if we've hit any rate limits recently
            rate_limits = api_client.check_rate_limit_status()
            
            if rate_limits:
                # Look for endpoints close to limit
                safe_to_proceed = True
                for category, endpoints in rate_limits.items():
                    for endpoint, limits in endpoints.items():
                        if limits.get('remaining', 100) < 20:  # Maintain a buffer of 20 calls
                            logger.warning(f"Rate limit buffer reached for {endpoint}. Skipping engagement.")
                            safe_to_proceed = False
                            break
                
                if not safe_to_proceed:
                    logger.info("Engagement deferred due to rate limit concerns.")
                    return
            
            # If safe, proceed with engagement
            xai_headers = api_client.initialize_xai_client()
            result = scheduler.engage_with_posts(readonly_client or x_client, xai_headers)
            logger.info(f"Engagement completed: {result}")
        except Exception as e:
            logger.error(f"Error in safe engagement: {e}")
    
    # Schedule engagement every 8 hours
    scheduler_instance.add_job(
        safe_engagement,
        IntervalTrigger(hours=8),
        id='engagement_task_8h'
    )
    
    # Also schedule daily backup at 2 AM UTC
    scheduler_instance.add_job(
        backup.backup_db,
        CronTrigger(hour=2, minute=0),
        id='database_backup'
    )
    
    scheduler_instance.start()
    logger.info("Scheduler started successfully (full mode with engagement)")
    
    # Keep the process alive
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