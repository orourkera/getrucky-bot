# health.py

import logging
import sqlite3
import os
from datetime import datetime, timedelta
import api_client
from config import get_config

logger = logging.getLogger(__name__)

# Database paths
INTERACTION_LOG_DB = '/tmp/interaction_log.db'
ANALYTICS_DB = '/tmp/analytics.db'
MODEL_CACHE_DB = '/tmp/model_cache.db'
PUN_LIBRARY_DB = '/tmp/pun_library.db'

def check_database_health():
    """Check the health of all SQLite databases."""
    databases = {
        'interaction_log': INTERACTION_LOG_DB,
        'analytics': ANALYTICS_DB,
        'model_cache': MODEL_CACHE_DB,
        'pun_library': PUN_LIBRARY_DB
    }
    
    health_status = {}
    for db_name, db_path in databases.items():
        try:
            # Auto-initialize databases if they don't exist
            if not os.path.exists(db_path):
                logger.warning(f"Database {db_name} not found, auto-initializing...")
                try:
                    # Import the backup module to avoid circular imports
                    import backup
                    backup.initialize_databases()
                    # If we successfully initialized, update the path and continue
                    if os.path.exists(db_path):
                        logger.info(f"Successfully auto-initialized {db_name}")
                    else:
                        # Add a dummy record to force database creation
                        try:
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            if db_name == 'interaction_log':
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
                                cursor.execute(
                                    "INSERT OR IGNORE INTO logs (tweet_id, reply_text, sentiment, content_type, timestamp, user_handle) VALUES (?, ?, ?, ?, ?, ?)",
                                    ("init123", "Health check initialization", "neutral", "system", datetime.utcnow().isoformat(), "system")
                                )
                            elif db_name == 'analytics':
                                cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS metrics (
                                        post_id TEXT PRIMARY KEY,
                                        likes INTEGER,
                                        retweets INTEGER,
                                        replies INTEGER,
                                        timestamp TIMESTAMP
                                    )
                                """)
                                cursor.execute(
                                    "INSERT OR IGNORE INTO metrics (post_id, likes, retweets, replies, timestamp) VALUES (?, ?, ?, ?, ?)",
                                    ("init123", 0, 0, 0, datetime.utcnow().isoformat())
                                )
                            elif db_name == 'model_cache':
                                cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS cache (
                                        prompt TEXT PRIMARY KEY,
                                        response TEXT,
                                        timestamp TIMESTAMP
                                    )
                                """)
                                cursor.execute(
                                    "INSERT OR IGNORE INTO cache (prompt, response, timestamp) VALUES (?, ?, ?)",
                                    ("health_check", "Database initialized by health check", datetime.utcnow().isoformat())
                                )
                            elif db_name == 'pun_library':
                                cursor.execute("""
                                    CREATE TABLE IF NOT EXISTS templates (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        text TEXT NOT NULL,
                                        type TEXT NOT NULL,
                                        category TEXT NOT NULL
                                    )
                                """)
                                cursor.execute(
                                    "INSERT OR IGNORE INTO templates (text, type, category) VALUES (?, ?, ?)",
                                    ("Ruck it up! 🥾 #GetRucky", "post", "pun")
                                )
                            conn.commit()
                            conn.close()
                            logger.info(f"Created minimal {db_name} database during health check")
                        except Exception as init_error:
                            logger.error(f"Error during in-line database initialization: {init_error}")
                except ImportError:
                    logger.error(f"Failed to import backup module for database initialization")
                    
            # Now check if we can access the database (it should exist now)
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Set status to healthy by default if we can connect
                health_status[db_name] = {'status': 'healthy'}
                
                # Additional checks for each database
                try:
                    if db_name == 'interaction_log':
                        cursor.execute("SELECT COUNT(*) FROM logs")
                        count = cursor.fetchone()[0]
                        health_status[db_name]['total_records'] = count
                    elif db_name == 'analytics':
                        cursor.execute("SELECT COUNT(*) FROM metrics")
                        count = cursor.fetchone()[0]
                        health_status[db_name]['total_metrics'] = count
                    elif db_name == 'model_cache':
                        cursor.execute("SELECT COUNT(*) FROM cache")
                        count = cursor.fetchone()[0]
                        health_status[db_name]['cached_responses'] = count
                    elif db_name == 'pun_library':
                        cursor.execute("SELECT COUNT(*) FROM templates")
                        count = cursor.fetchone()[0]
                        health_status[db_name]['total_templates'] = count
                except sqlite3.OperationalError as e:
                    # Tables may not exist yet, consider as initializing
                    health_status[db_name] = {
                        'status': 'initializing',
                        'message': f'Database exists but tables not ready: {str(e)}'
                    }
                
                conn.close()
            else:
                # After all our attempts, the database still doesn't exist
                health_status[db_name] = {
                    'status': 'error',
                    'message': f'Database file still missing after initialization attempts'
                }
        except Exception as e:
            health_status[db_name] = {
                'status': 'error',
                'message': str(e)
            }
    
    return health_status

def check_api_health(x_client):
    """Check the health of external APIs."""
    api_status = {}
    
    # Check X API - safely handle non-verifying clients
    try:
        # Check if the client has wait_on_rate_limit set to False
        # If so, don't make API calls that might rate limit
        client_has_rate_limit = getattr(x_client, '_wait_on_rate_limit', True)
        
        if not client_has_rate_limit:
            # For dashboard clients, just report status without checking
            api_status['x_api'] = {
                'status': 'unknown',
                'message': 'Client initialized with wait_on_rate_limit=False, skipping health check'
            }
        else:
            # Try to get user profile - only for clients set to wait on rate limit
            try:
                user = x_client.get_me()
                if hasattr(user, 'data') and user.data:
                    api_status['x_api'] = {
                        'status': 'healthy',
                        'username': user.data.username,
                        'id': user.data.id
                    }
                else:
                    api_status['x_api'] = {
                        'status': 'error',
                        'message': 'Could not fetch user data'
                    }
            except Exception as x_error:
                api_status['x_api'] = {
                    'status': 'error',
                    'message': str(x_error)
                }
    except Exception as e:
        api_status['x_api'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check xAI API
    try:
        xai_headers = {'Authorization': f'Bearer {get_config("XAI_API_KEY")}'}
        test_prompt = "Generate a test response, <10 characters."
        response = api_client.generate_text(xai_headers, test_prompt)
        api_status['xai_api'] = {
            'status': 'healthy',
            'test_response': response[:10] if response else None
        }
    except Exception as e:
        api_status['xai_api'] = {
            'status': 'error',
            'message': str(e)
        }
    
    return api_status

def check_system_health():
    """Check system resources and environment."""
    try:
        # Check memory usage
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_status = {
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent_used': memory.percent
            },
            'disk': {
                'total': disk.total,
                'free': disk.free,
                'percent_used': disk.percent
            },
            'environment': {
                'python_version': os.sys.version,
                'heroku_dyno': os.environ.get('DYNO', 'unknown'),
                'database_url': bool(os.environ.get('DATABASE_URL')),
                'xai_api_key': bool(get_config('XAI_API_KEY')),
                'x_api_key': bool(get_config('X_API_KEY'))
            }
        }
        return system_status
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def get_health_status(x_client):
    """Get comprehensive health status of the bot."""
    try:
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'databases': check_database_health(),
            'apis': check_api_health(x_client),
            'system': check_system_health()
        }
        
        # Determine overall status
        # Count status types
        status_counts = {'healthy': 0, 'initializing': 0, 'error': 0, 'unknown': 0}
        
        # Count database statuses
        for db in health_status['databases'].values():
            status_counts[db['status']] = status_counts.get(db['status'], 0) + 1
            
        # Count API statuses
        for api in health_status['apis'].values():
            status_counts[api['status']] = status_counts.get(api['status'], 0) + 1
        
        # Determine overall status
        if status_counts['error'] > 0:
            if status_counts['healthy'] > 0:
                overall_status = 'degraded'
            else:
                overall_status = 'error'
        elif status_counts['initializing'] > 0:
            overall_status = 'initializing'
        elif status_counts['unknown'] > 0 and status_counts['healthy'] > 0:
            overall_status = 'healthy'  # Dashboard mode is fine
        else:
            overall_status = 'healthy'
        
        health_status['overall_status'] = overall_status
        
        return health_status
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'error',
            'error': str(e)
        } 