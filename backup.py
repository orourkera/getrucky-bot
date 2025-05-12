# backup.py

import os
import sqlite3
import psycopg2
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Heroku Postgres connection details from environment
DATABASE_URL = os.getenv('DATABASE_URL', '')

# SQLite database files in Heroku ephemeral filesystem
DB_FILES = {
    'pun_library': '/tmp/pun_library.db',
    'interaction_log': '/tmp/interaction_log.db',
    'analytics': '/tmp/analytics.db',
    'model_cache': '/tmp/model_cache.db'
}

def backup_db():
    """Backup SQLite databases to Heroku Postgres."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set. Cannot perform backup.")
        return False
    
    try:
        # Connect to Heroku Postgres
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Create backups table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                db_name TEXT,
                data BYTEA,
                timestamp TIMESTAMP
            )
        """)
        
        backup_time = datetime.utcnow()
        for db_name, db_path in DB_FILES.items():
            if os.path.exists(db_path):
                with open(db_path, 'rb') as f:
                    db_data = f.read()
                cur.execute(
                    "INSERT INTO backups (db_name, data, timestamp) VALUES (%s, %s, %s)",
                    (db_name, psycopg2.Binary(db_data), backup_time)
                )
                logger.info(f"Backed up {db_name} to Heroku Postgres")
            else:
                logger.warning(f"Database file {db_path} not found for backup")
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database backup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during database backup: {e}")
        return False

def restore_db(db_name):
    """Restore a specific SQLite database from Heroku Postgres."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set. Cannot perform restore.")
        return False
    
    if db_name not in DB_FILES:
        logger.error(f"Invalid database name: {db_name}")
        return False
    
    db_path = DB_FILES[db_name]
    try:
        # Connect to Heroku Postgres
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Fetch the latest backup for the specified database
        cur.execute("""
            SELECT data FROM backups
            WHERE db_name = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (db_name,))
        result = cur.fetchone()
        
        if result:
            with open(db_path, 'wb') as f:
                f.write(result[0])
            logger.info(f"Restored {db_name} from Heroku Postgres to {db_path}")
            cur.close()
            conn.close()
            return True
        else:
            logger.warning(f"No backup found for {db_name}")
            cur.close()
            conn.close()
            return False
    except Exception as e:
        logger.error(f"Error restoring database {db_name}: {e}")
        return False

def initialize_databases():
    """Initialize SQLite databases with schemas if they don't exist."""
    try:
        # Ensure /tmp directory exists and has proper permissions
        os.makedirs('/tmp', exist_ok=True)
        os.chmod('/tmp', 0o777)  # Full permissions for Heroku ephemeral filesystem
        
        # Pun Library DB
        conn = sqlite3.connect(DB_FILES['pun_library'])
        conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Initialized pun_library.db")
        
        # Interaction Log DB
        conn = sqlite3.connect(DB_FILES['interaction_log'])
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                tweet_id TEXT PRIMARY KEY,
                reply_text TEXT,
                sentiment TEXT,
                content_type TEXT,
                timestamp TIMESTAMP,
                mention_timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Initialized interaction_log.db")
        
        # Analytics DB
        conn = sqlite3.connect(DB_FILES['analytics'])
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                post_id TEXT PRIMARY KEY,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                timestamp TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                tweet_id TEXT,
                action TEXT,
                timestamp TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                text TEXT,
                reason TEXT,
                timestamp TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Initialized analytics.db")
        
        # Model Cache DB
        conn = sqlite3.connect(DB_FILES['model_cache'])
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                prompt TEXT PRIMARY KEY,
                response TEXT,
                timestamp TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Initialized model_cache.db")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing databases: {e}")
        return False 