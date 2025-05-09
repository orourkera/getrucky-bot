# main.py

import logging
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import api_client
import scheduler
import interaction_handler
import cross_post

# Configure logging for Heroku Logplex
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to initialize and run the AI Marketing Bot."""
    logger.info("Starting AI Marketing Bot for @getrucky")
    
    try:
        # Initialize API clients
        x_client = api_client.initialize_x_client()
        app_client = api_client.initialize_app_client()
        xai_client = api_client.initialize_xai_client()
        logger.info("API clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        sys.exit(1)
    
    # Initialize scheduler for posts and engagement
    bot_scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.schedule_posts(bot_scheduler, x_client, app_client, xai_client)
    scheduler.schedule_engagement(bot_scheduler, x_client, xai_client)
    bot_scheduler.start()
    logger.info("Scheduler started for posts and engagement tasks")
    
    # Start monitoring mentions
    try:
        interaction_handler.monitor_mentions(x_client, xai_client)
    except Exception as e:
        logger.error(f"Error in monitoring mentions: {e}")
        # Attempt to restart monitoring
        logger.info("Restarting mention monitoring...")
        interaction_handler.monitor_mentions(x_client, xai_client)
    
    logger.info("AI Marketing Bot is fully operational")

if __name__ == "__main__":
    main() 