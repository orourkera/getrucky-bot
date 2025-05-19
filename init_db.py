#!/usr/bin/env python
# init_db.py - Script to manually initialize databases and ensure they show as healthy in the dashboard

import logging
import sqlite3
import os
import sys
import time
from datetime import datetime
import backup
from config import SQLITE_DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database paths
DB_PATHS = {
    'pun_library': f"{SQLITE_DB_PATH}/pun_library.db",
    'interaction_log': f"{SQLITE_DB_PATH}/interaction_log.db", 
    'analytics': f"{SQLITE_DB_PATH}/analytics.db",
    'model_cache': f"{SQLITE_DB_PATH}/model_cache.db"
}

def ensure_directory_exists():
    """Ensure the database directory exists."""
    try:
        os.makedirs(SQLITE_DB_PATH, exist_ok=True)
        logger.info(f"Database directory {SQLITE_DB_PATH} is available")
        return True
    except Exception as e:
        logger.error(f"Failed to create database directory: {e}")
        return False

def initialize_pun_library_db():
    """Initialize pun_library.db with schema and sample data."""
    try:
        conn = sqlite3.connect(DB_PATHS['pun_library'])
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL
            )
        """)
        
        # Add sample data if table is empty
        cursor.execute("SELECT COUNT(*) FROM templates")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample templates
            sample_templates = [
                ("Ruck it up! 🥾 #GetRucky", "post", "pun"),
                ("Time to ruck and roll! 🥾 #GetRucky", "post", "pun"),
                ("What's your favorite rucking route? 🥾 #GetRucky", "post", "poll"),
                ("Rucking builds mental and physical strength! 🥾 #GetRucky", "post", "theme"),
                ("When the trail gets tough, the ruckers get going! 🥾 #GetRucky", "post", "meme"),
                ("Great job on your ruck! Keep crushing it! 🥾 #GetRucky", "post", "shoutout"),
                ("Awesome progress! 💪 #RuckLife", "reply", "positive"),
                ("Sorry to hear that. Keep pushing! 🥾", "reply", "negative"),
                ("Great question! Rucking is weight training + walking. 🥾", "reply", "question"),
                ("Thanks for sharing! 🥾 #GetRucky", "reply", "neutral")
            ]
            
            cursor.executemany(
                "INSERT INTO templates (text, type, category) VALUES (?, ?, ?)", 
                sample_templates
            )
            logger.info(f"Added {len(sample_templates)} sample templates to pun_library")
        
        conn.commit()
        conn.close()
        logger.info("Successfully initialized pun_library.db")
        return True
    except Exception as e:
        logger.error(f"Error initializing pun_library.db: {e}")
        return False

def initialize_interaction_log_db():
    """Initialize interaction_log.db with schema and sample data."""
    try:
        conn = sqlite3.connect(DB_PATHS['interaction_log'])
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                tweet_id TEXT PRIMARY KEY,
                reply_text TEXT,
                sentiment TEXT,
                content_type TEXT,
                timestamp TIMESTAMP,
                mention_timestamp TEXT,
                reply_to_tweet_id TEXT,
                user_handle TEXT
            )
        """)
        
        # Add sample data if table is empty
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample log entry
            current_time = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO logs (tweet_id, reply_text, sentiment, content_type, timestamp, user_handle) VALUES (?, ?, ?, ?, ?, ?)",
                ("123456", "Sample reply text", "positive", "reply", current_time, "getrucky")
            )
            logger.info("Added sample entry to interaction_log")
        
        conn.commit()
        conn.close()
        logger.info("Successfully initialized interaction_log.db")
        return True
    except Exception as e:
        logger.error(f"Error initializing interaction_log.db: {e}")
        return False

def initialize_analytics_db():
    """Initialize analytics.db with schema and sample data."""
    try:
        conn = sqlite3.connect(DB_PATHS['analytics'])
        cursor = conn.cursor()
        
        # Create metrics table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                post_id TEXT PRIMARY KEY,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                timestamp TIMESTAMP
            )
        """)
        
        # Create engagement table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                tweet_id TEXT,
                action TEXT,
                timestamp TIMESTAMP
            )
        """)
        
        # Create flags table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                text TEXT,
                reason TEXT,
                timestamp TIMESTAMP
            )
        """)
        
        # Add sample data if metrics table is empty
        cursor.execute("SELECT COUNT(*) FROM metrics")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample metrics entry
            current_time = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO metrics (post_id, likes, retweets, replies, timestamp) VALUES (?, ?, ?, ?, ?)",
                ("123456", 5, 2, 1, current_time)
            )
            logger.info("Added sample entry to analytics metrics")
        
        # Add sample data if engagement table is empty
        cursor.execute("SELECT COUNT(*) FROM engagement")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample engagement entry
            current_time = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO engagement (tweet_id, action, timestamp) VALUES (?, ?, ?)",
                ("123456", "like", current_time)
            )
            logger.info("Added sample entry to analytics engagement")
        
        conn.commit()
        conn.close()
        logger.info("Successfully initialized analytics.db")
        return True
    except Exception as e:
        logger.error(f"Error initializing analytics.db: {e}")
        return False

def initialize_model_cache_db():
    """Initialize model_cache.db with schema and sample data."""
    try:
        conn = sqlite3.connect(DB_PATHS['model_cache'])
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                prompt TEXT PRIMARY KEY,
                response TEXT,
                timestamp TIMESTAMP
            )
        """)
        
        # Add sample data if table is empty
        cursor.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add sample cache entry
            current_time = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO cache (prompt, response, timestamp) VALUES (?, ?, ?)",
                ("Explain briefly why rucking is good for fitness.", 
                 "Rucking combines strength training and cardio by adding weight to walking, improving endurance, burning calories, and building muscle strength.", 
                 current_time)
            )
            logger.info("Added sample entry to model_cache")
        
        conn.commit()
        conn.close()
        logger.info("Successfully initialized model_cache.db")
        return True
    except Exception as e:
        logger.error(f"Error initializing model_cache.db: {e}")
        return False

def initialize_engagement_table():
    """Initialize the engagement table in analytics.db to track likes, comments, and retweets."""
    try:
        conn = sqlite3.connect(DB_PATHS['analytics'])
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                tweet_id TEXT,
                action TEXT,
                timestamp TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Successfully initialized engagement table in analytics.db")
        return True
    except Exception as e:
        logger.error(f"Error initializing engagement table: {e}")
        return False

def main():
    """Main function to initialize all databases."""
    logger.info("Starting database initialization...")
    
    # Ensure database directory exists
    if not ensure_directory_exists():
        sys.exit(1)
    
    # Initialize all databases
    initialize_pun_library_db()
    initialize_interaction_log_db()
    initialize_analytics_db()
    initialize_model_cache_db()
    
    # Call the function to initialize the engagement table
    initialize_engagement_table()
    
    logger.info("Database initialization completed.")
    
if __name__ == "__main__":
    main() 