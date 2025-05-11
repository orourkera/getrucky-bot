# main.py

import logging
import sys
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import api_client
import scheduler
import interaction_handler
import cross_post
import backup
import ai_model
import moderation
import analytics
from flask import Flask, jsonify
from health import get_health_status
from config import get_config, validate_config
import threading

# Configure logging for Heroku Logplex
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

def main():
    """Main function to initialize and run the AI Marketing Bot."""
    logger.info("Starting AI Marketing Bot for @getrucky")
    
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
    
    try:
        # Initialize API clients
        logger.info("Initializing API clients")
        x_client = api_client.initialize_x_client()
        app_client = api_client.initialize_app_client()
        xai_client = api_client.initialize_xai_client()
        logger.info("API clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        sys.exit(1)
    
    # If DATABASE_URL is set, try to restore databases from Postgres
    if os.getenv('DATABASE_URL'):
        logger.info("Attempting to restore databases from Heroku Postgres")
        for db_name in ['pun_library', 'interaction_log', 'analytics', 'model_cache']:
            try:
                backup.restore_db(db_name)
            except Exception as e:
                logger.warning(f"Failed to restore {db_name}: {e}")
    
    # Initialize scheduler for posts and engagement
    logger.info("Initializing scheduler")
    scheduler_instance = BackgroundScheduler()
    
    # Schedule posts
    for hour in get_config('POST_TIMES'):
        scheduler_instance.add_job(
            scheduler.schedule_posts,
            CronTrigger(hour=hour, minute=0),
            args=[x_client, xai_client]
        )
    
    # Schedule engagement tasks
    scheduler_instance.add_job(
        scheduler.schedule_engagement,
        CronTrigger(minute='*/5'),  # Every 5 minutes
        args=[x_client]
    )
    
    # Start scheduler
    scheduler_instance.start()
    logger.info("Scheduler started successfully")

    # Start monitoring mentions in a background thread
    logger.info("Starting mention monitoring in background thread")
    threading.Thread(target=interaction_handler.monitor_mentions, args=(x_client, xai_client), daemon=True).start()

    # Start cross-posting in a background thread
    logger.info("Starting cross-posting in background thread")
    threading.Thread(target=cross_post.engage_with_posts, args=(x_client, xai_client), daemon=True).start()

    # Run Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        health_status = get_health_status(x_client)
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    main() 