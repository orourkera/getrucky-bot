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

# Initialize Flask app
app = Flask(__name__)

# Initialize X client lazily
x_client = None

def get_x_client():
    """Lazy initialization of X client."""
    global x_client
    if x_client is None:
        try:
            x_client = api_client.initialize_x_client()
        except Exception as e:
            logger.error(f"Failed to initialize X client: {e}")
            return None
    return x_client

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
    try:
        # Get health status
        client = get_x_client()
        health_status = get_health_status(client) if client else {'status': 'error', 'message': 'X client not initialized'}
        
        # Get engagement stats
        engagement_stats = get_engagement_stats()
        
        # Get content stats
        content_stats = get_content_stats()
        
        # Get weekly summary
        try:
            weekly_summary = analytics.summarize_interactions()
        except Exception as e:
            logger.error(f"Error getting weekly summary: {e}")
            weekly_summary = {
                'avg_response_time': 0,
                'total_interactions': 0,
                'engagement_rate': 0
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
    try:
        client = get_x_client()
        return jsonify({
            'health': get_health_status(client) if client else {'status': 'error', 'message': 'X client not initialized'},
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
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 