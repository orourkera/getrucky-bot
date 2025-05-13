# main.py

import logging
import sys
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
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


def initialize_clients():
    """Initialize API clients with proper error handling and retries."""
    global x_client
    try:
        logger.info("Initializing API clients")
        x_client = api_client.initialize_x_client(max_retries=5, retry_delay=10, verify=False)
        logger.info("API clients initialized successfully")
        return x_client
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """Main function to initialize and run the AI Marketing Bot (posting only)."""
    global x_client
    logger.info("Starting AI Marketing Bot for @getrucky (posting only mode)")
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
    # Initialize scheduler for posts only
    logger.info("Initializing scheduler (posting only)")
    scheduler_instance = BackgroundScheduler()
    # Schedule 5 random posts per day
    logger.info("Scheduling 5 random posts per day")
    post_times = get_post_times()[:5]
    for hour, minute in post_times:
        scheduler_instance.add_job(
            scheduler.post_regular_content,
            CronTrigger(hour=hour, minute=minute),
            args=[x_client, api_client.initialize_xai_client()],
            id=f'regular_post_{hour}_{minute}'
        )
        logger.info(f"Scheduled regular post at {hour}:{minute:02d} UTC")
    scheduler_instance.start()
    logger.info("Scheduler started successfully (posting only mode)")
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
        return jsonify({'status': 'ok', 'message': 'Posting only mode'})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    main() 