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
import traceback

# Configure logging for Heroku Logplex
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables for sharing state
x_client = None
authenticated_user_id = None

def initialize_clients():
    """Initialize API clients with proper error handling and retries."""
    global x_client, authenticated_user_id
    
    try:
        # Initialize API clients with retries
        logger.info("Initializing API clients")
        x_client = api_client.initialize_x_client(max_retries=5, retry_delay=10, verify=False)
        app_client = api_client.initialize_app_client()
        xai_client = api_client.initialize_xai_client()
        
        # Get the authenticated user's ID once (and log it)
        try:
            me_response = x_client.get_me()
            if not me_response or not hasattr(me_response, 'data') or not me_response.data:
                logger.error("Failed to get authenticated user ID. Retrying...")
                time.sleep(5)
                me_response = x_client.get_me()  # One retry
                
            if me_response and hasattr(me_response, 'data') and me_response.data:
                authenticated_user_id = me_response.data.id
                logger.info(f"Authenticated user ID: {authenticated_user_id} for @{me_response.data.username}")
            else:
                logger.error("Failed to get authenticated user ID after retry. Exiting.")
                sys.exit(1)
        except Exception as user_id_error:
            logger.error(f"Error getting authenticated user ID: {user_id_error}")
            sys.exit(1)
        
        logger.info("API clients initialized successfully")
        return x_client, app_client, xai_client, authenticated_user_id
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """Main function to initialize and run the AI Marketing Bot."""
    global x_client, authenticated_user_id
    
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
    
    # Initialize API clients
    x_client, app_client, xai_client, authenticated_user_id = initialize_clients()
    
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
    logger.info("Scheduling posts")
    for hour in get_config('POST_TIMES'):
        scheduler_instance.add_job(
            scheduler.schedule_posts,
            CronTrigger(hour=hour, minute=0),
            args=[scheduler_instance, x_client, app_client, xai_client]
        )
    
    # Schedule engagement tasks
    logger.info("Scheduling engagement tasks")
    scheduler_instance.add_job(
        scheduler.schedule_engagement,
        CronTrigger(hour='*/2'),  # Every 2 hours
        args=[scheduler_instance, x_client, xai_client]
    )
    
    # Start scheduler
    scheduler_instance.start()
    logger.info("Scheduler started successfully")

    # Start monitoring mentions in a background thread
    logger.info("Starting mention monitoring in background thread")
    mention_thread = threading.Thread(
        target=interaction_handler.monitor_mentions, 
        args=(x_client, xai_client, authenticated_user_id), 
        daemon=True,
        name="MentionMonitoringThread"
    )
    mention_thread.start()

    # Start cross-posting in a background thread
    logger.info("Starting cross-posting in background thread")
    crosspost_thread = threading.Thread(
        target=cross_post.engage_with_posts, 
        args=(x_client, xai_client), 
        daemon=True,
        name="CrossPostThread"
    )
    crosspost_thread.start()

    # Log that workers are started
    logger.info("All background processes started successfully")
    
    # Run Flask app on worker dyno
    # Only run the Flask app if this is the web dyno (identified by PORT variable being set)
    if 'PORT' in os.environ:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        # If this is a worker dyno, just keep the process alive
        logger.info("Running as worker process - keeping process alive")
        while True:
            try:
                time.sleep(60)  # Sleep for a minute and then check if threads are still running
                if not mention_thread.is_alive():
                    logger.error("Mention monitoring thread died, restarting...")
                    mention_thread = threading.Thread(
                        target=interaction_handler.monitor_mentions, 
                        args=(x_client, xai_client, authenticated_user_id), 
                        daemon=True,
                        name="MentionMonitoringThread"
                    )
                    mention_thread.start()
                
                if not crosspost_thread.is_alive():
                    logger.error("Cross-post thread died, restarting...")
                    crosspost_thread = threading.Thread(
                        target=cross_post.engage_with_posts, 
                        args=(x_client, xai_client), 
                        daemon=True,
                        name="CrossPostThread"
                    )
                    crosspost_thread.start()
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Sleep and continue

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