# dashboard.py

import logging
from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import analytics
from health import get_health_status
import api_client
import os
from config import get_config, validate_config, SQLITE_DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine the absolute path to the directory of dashboard.py
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT, 'templates')

# Initialize Flask app, explicitly setting template_folder
app = Flask("dashboard_app", template_folder=TEMPLATE_FOLDER)

# Global X client and initialization status
x_client_global = None
x_client_init_error_global = None

def initialize_global_x_client():
    """Initialize the global X client once."""
    global x_client_global, x_client_init_error_global
    # Try to initialize only if it hasn't been attempted or if there was no error previously
    # Or, more simply, just try once.
    if x_client_global is None and x_client_init_error_global is None:
        logger.info("Dashboard: Attempting to initialize global X client...")
        try:
            x_client_global = api_client.initialize_x_client()
            if x_client_global:
                logger.info("Dashboard: Global X client initialized successfully.")
            else:
                x_client_init_error_global = "Failed to initialize X client (returned None)."
                logger.error(x_client_init_error_global)
        except Exception as e:
            x_client_init_error_global = f"Dashboard: Failed to initialize global X client: {e}"
            logger.error(x_client_init_error_global)
            x_client_global = None # Ensure client is None on error

# Call this when the app starts (or before the first request in a real server)
# For development server, this will run when the module is loaded.
initialize_global_x_client()

def get_engagement_stats():
    """Get engagement statistics from analytics database."""
    try:
        db_path = os.path.join(SQLITE_DB_PATH, 'analytics.db')
        if not os.path.exists(db_path):
            logger.warning(f"Analytics database not found at {db_path}")
            return {
                'engagements': {'total': 0, 'likes': 0, 'retweets': 0, 'replies': 0},
                'interactions': {'total': 0, 'avg_response_time': 0}
            }
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get last 24 hours of engagement
        cursor.execute("""
            SELECT 
                COUNT(*) as total_engagements,
                SUM(CASE WHEN action = 'like' THEN 1 ELSE 0 END) as likes,
                SUM(CASE WHEN action = 'retweet' THEN 1 ELSE 0 END) as retweets,
                SUM(CASE WHEN action = 'reply' THEN 1 ELSE 0 END) as replies
            FROM engagement
            WHERE timestamp > datetime('now', '-1 day')
        """)
        engagement = cursor.fetchone()
        
        # Get last 24 hours of interactions
        cursor.execute("""
            SELECT 
                COUNT(*) as total_interactions,
                AVG(CASE 
                    WHEN mention_timestamp IS NOT NULL 
                    THEN (julianday(timestamp) - julianday(mention_timestamp)) * 24 * 60 
                    ELSE NULL 
                END) as avg_response_time
            FROM logs
            WHERE timestamp > datetime('now', '-1 day')
        """)
        interactions = cursor.fetchone()
        
        conn.close()
        
        return {
            'engagements': {
                'total': engagement[0] if engagement[0] else 0,
                'likes': engagement[1] if engagement[1] else 0,
                'retweets': engagement[2] if engagement[2] else 0,
                'replies': engagement[3] if engagement[3] else 0
            },
            'interactions': {
                'total': interactions[0] if interactions[0] else 0,
                'avg_response_time': round(interactions[1], 2) if interactions[1] else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting engagement stats: {e}")
        return {
            'engagements': {'total': 0, 'likes': 0, 'retweets': 0, 'replies': 0},
            'interactions': {'total': 0, 'avg_response_time': 0}
        }

def get_content_stats():
    """Get content generation statistics."""
    try:
        db_path = os.path.join(SQLITE_DB_PATH, 'analytics.db')
        if not os.path.exists(db_path):
            logger.warning(f"Analytics database not found at {db_path}")
            return {'content_types': {}, 'sentiments': {}}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get content type distribution
        cursor.execute("""
            SELECT 
                content_type,
                COUNT(*) as count
            FROM metrics
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY content_type
        """)
        content_types = cursor.fetchall()
        
        # Get sentiment distribution
        cursor.execute("""
            SELECT 
                sentiment,
                COUNT(*) as count
            FROM logs
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY sentiment
        """)
        sentiments = cursor.fetchall()
        
        conn.close()
        
        return {
            'content_types': dict(content_types) if content_types else {},
            'sentiments': dict(sentiments) if sentiments else {}
        }
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        return {'content_types': {}, 'sentiments': {}}

@app.route('/')
def dashboard():
    """Render the main dashboard."""
    global x_client_global, x_client_init_error_global
    try:
        current_x_client = x_client_global
        health_status = None
        if current_x_client:
            try:
                health_status = get_health_status(current_x_client)
            except Exception as he:
                logger.error(f"Error getting health status from dashboard: {he}")
                health_status = {'status': 'error', 'message': f'Error in get_health_status: {he}'}
        else:
            health_status = {'status': 'error', 'message': x_client_init_error_global or 'X client not initialized (global)'}
        
        # Get engagement stats (ensure these are fast)
        engagement_stats = get_engagement_stats()
        
        # Get content stats (ensure these are fast)
        content_stats = get_content_stats()
        
        # Get weekly summary (ensure this is fast or handled differently)
        try:
            weekly_summary = analytics.summarize_interactions()
        except Exception as e_summary:
            logger.error(f"Error getting weekly summary for dashboard: {e_summary}")
            weekly_summary = {
                'avg_response_time': 0,
                'total_interactions': 0,
                'engagement_rate': 0,
                'error': str(e_summary)
            }
        
        return render_template(
            'dashboard.html',
            health=health_status,
            engagement=engagement_stats,
            content=content_stats,
            weekly=weekly_summary
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics."""
    global x_client_global, x_client_init_error_global
    try:
        current_x_client = x_client_global
        health_data = None
        if current_x_client:
            try:
                health_data = get_health_status(current_x_client)
            except Exception as he_api:
                logger.error(f"Error getting health status for API: {he_api}")
                health_data = {'status': 'error', 'message': f'Error in get_health_status for API: {he_api}'}
        else:
            health_data = {'status': 'error', 'message': x_client_init_error_global or 'X client not initialized (global)'}

        return jsonify({
            'health': health_data,
            'engagement': get_engagement_stats(),
            'content': get_content_stats(),
            'weekly': analytics.summarize_interactions()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Validate configuration
    config_status = validate_config()
    if not all(config_status.values()):
        logger.error("Missing required environment variables. Please check the configuration.")
    else:
        logger.info("Configuration validated successfully")
    
    # Note: initialize_global_x_client() is already called at module load time.
    # For a production WSGI server, you might use @app.before_first_request or similar,
    # but for Heroku with gunicorn (default for Flask), module-level init is fine.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 