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

# Configure logging for Heroku Logplex
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to initialize and run the AI Marketing Bot."""
    logger.info("Starting AI Marketing Bot for @getrucky")
    
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
    bot_scheduler = BackgroundScheduler(timezone="UTC")
    
    # Schedule posts and engagement tasks
    scheduler.schedule_posts(bot_scheduler, x_client, app_client, xai_client)
    scheduler.schedule_engagement(bot_scheduler, x_client, xai_client)
    
    # Schedule maintenance tasks
    schedule_maintenance_tasks(bot_scheduler, x_client)
    
    # Start the scheduler
    bot_scheduler.start()
    logger.info("Scheduler started for posts, engagement, and maintenance tasks")
    
    # Start monitoring mentions
    try:
        logger.info("Starting mention monitoring")
        interaction_handler.monitor_mentions(x_client, xai_client)
    except Exception as e:
        logger.error(f"Error in monitoring mentions: {e}")
        # Attempt to restart monitoring
        logger.info("Restarting mention monitoring...")
        interaction_handler.monitor_mentions(x_client, xai_client)
    
    logger.info("AI Marketing Bot is fully operational")

def schedule_maintenance_tasks(scheduler, x_client):
    """Schedule maintenance tasks like backups, cache cleanup, and analytics."""
    
    # Daily database backup
    scheduler.add_job(
        backup.backup_db,
        CronTrigger(hour=3, minute=0),  # Run at 3 AM UTC
        id='daily_backup'
    )
    logger.info("Scheduled daily database backup at 3:00 UTC")
    
    # Clear expired cache entries daily
    scheduler.add_job(
        ai_model.clear_expired_cache_entries,
        CronTrigger(hour=2, minute=30),  # Run at 2:30 AM UTC
        id='clear_cache'
    )
    logger.info("Scheduled daily cache cleanup at 2:30 UTC")
    
    # Track engagement metrics every 4 hours
    scheduler.add_job(
        lambda: analytics.track_engagement(x_client),
        'interval',
        hours=4,
        id='track_engagement'
    )
    logger.info("Scheduled engagement tracking every 4 hours")
    
    # Generate and log weekly summary every Sunday
    scheduler.add_job(
        analytics.log_weekly_summary,
        CronTrigger(day_of_week=6, hour=12, minute=0),  # Sunday at noon UTC
        id='weekly_summary'
    )
    logger.info("Scheduled weekly analytics summary on Sundays at 12:00 UTC")
    
    # Monitor API rate limits every hour
    scheduler.add_job(
        monitor_api_limits,
        'interval',
        hours=1,
        id='monitor_limits'
    )
    logger.info("Scheduled hourly API rate limit monitoring")

def monitor_api_limits():
    """Monitor API rate limits and log warnings if approaching limits."""
    api_types = ['x_tweet', 'x_like', 'x_retweet', 'x_search', 'xai']
    
    for api_type in api_types:
        is_limited, wait_time = moderation.rate_limit_check(api_type)
        
        if is_limited:
            logger.warning(f"API rate limit concern for {api_type}: {wait_time}s until reset")
    
    # Log API usage statistics
    usage_stats = moderation.get_api_usage()
    logger.info(f"API usage statistics (hourly): {usage_stats['hourly']}")

if __name__ == "__main__":
    main() 