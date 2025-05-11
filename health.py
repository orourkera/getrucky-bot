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
            if not os.path.exists(db_path):
                health_status[db_name] = {
                    'status': 'error',
                    'message': f'Database file not found: {db_path}'
                }
                continue
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if database is accessible and has expected tables
            if db_name == 'interaction_log':
                cursor.execute("SELECT COUNT(*) FROM logs WHERE timestamp > datetime('now', '-1 hour')")
                recent_interactions = cursor.fetchone()[0]
                health_status[db_name] = {
                    'status': 'healthy',
                    'recent_interactions': recent_interactions
                }
            elif db_name == 'analytics':
                cursor.execute("SELECT COUNT(*) FROM metrics WHERE timestamp > datetime('now', '-1 hour')")
                recent_metrics = cursor.fetchone()[0]
                health_status[db_name] = {
                    'status': 'healthy',
                    'recent_metrics': recent_metrics
                }
            elif db_name == 'model_cache':
                cursor.execute("SELECT COUNT(*) FROM cache WHERE timestamp > datetime('now', '-1 hour')")
                recent_cache = cursor.fetchone()[0]
                health_status[db_name] = {
                    'status': 'healthy',
                    'recent_cache_entries': recent_cache
                }
            elif db_name == 'pun_library':
                cursor.execute("SELECT COUNT(*) FROM templates")
                total_templates = cursor.fetchone()[0]
                health_status[db_name] = {
                    'status': 'healthy',
                    'total_templates': total_templates
                }
            
            conn.close()
        except Exception as e:
            health_status[db_name] = {
                'status': 'error',
                'message': str(e)
            }
    
    return health_status

def check_api_health(x_client):
    """Check the health of external APIs."""
    api_status = {}
    
    # Check X API
    try:
        # Try to get user profile
        user = x_client.get_me()
        api_status['x_api'] = {
            'status': 'healthy',
            'username': user.screen_name,
            'followers': user.followers_count
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
        all_healthy = all(
            db['status'] == 'healthy' 
            for db in health_status['databases'].values()
        ) and all(
            api['status'] == 'healthy' 
            for api in health_status['apis'].values()
        )
        
        health_status['overall_status'] = 'healthy' if all_healthy else 'degraded'
        
        return health_status
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'error',
            'error': str(e)
        } 