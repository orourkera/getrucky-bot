# analytics.py

import logging
import sqlite3
from datetime import datetime, timedelta
import api_client

logger = logging.getLogger(__name__)

# Database paths
ANALYTICS_DB = '/tmp/analytics.db'
INTERACTION_LOG_DB = '/tmp/interaction_log.db'

def track_engagement(x_client):
    """Track engagement metrics for @getrucky posts."""
    try:
        # Get the latest tweets from @getrucky
        tweets = x_client.user_timeline(screen_name='getrucky', count=50, tweet_mode='extended')
        
        engagement_data = []
        for tweet in tweets:
            post_id = tweet.id_str
            
            # Get engagement metrics
            metrics = {
                'post_id': post_id,
                'likes': tweet.favorite_count,
                'retweets': tweet.retweet_count,
                'replies': 0,  # API doesn't provide direct reply count, would need a separate search
                'timestamp': datetime.utcnow()
            }
            
            # Store metrics in database
            store_metrics(metrics)
            engagement_data.append(metrics)
        
        logger.info(f"Tracked engagement for {len(engagement_data)} @getrucky posts")
        return engagement_data
    except Exception as e:
        logger.error(f"Error tracking engagement: {e}")
        return []

def store_metrics(metrics):
    """Store engagement metrics in analytics.db."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Ensure the metrics table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                post_id TEXT PRIMARY KEY,
                likes INTEGER,
                retweets INTEGER,
                replies INTEGER,
                timestamp TIMESTAMP
            )
        """)
        
        # Insert or update metrics
        cursor.execute("""
            INSERT OR REPLACE INTO metrics (post_id, likes, retweets, replies, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            metrics['post_id'],
            metrics['likes'],
            metrics['retweets'],
            metrics['replies'],
            metrics['timestamp']
        ))
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored metrics for post {metrics['post_id']}")
        return True
    except Exception as e:
        logger.error(f"Error storing metrics: {e}")
        return False

def summarize_interactions(days=7):
    """Summarize interactions over the specified number of days."""
    try:
        # Get start date for the summary period
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Initialize summary data
        summary = {
            'period_days': days,
            'start_date': start_date,
            'end_date': datetime.utcnow().isoformat(),
            'total_interactions': 0,
            'sentiment': {'positive': 0, 'neutral': 0, 'negative': 0},
            'content_types': {},
            'engagement': {'total_likes': 0, 'total_retweets': 0, 'total_replies': 0},
            'engagement_actions': {'likes': 0, 'retweets': 0, 'comments': 0},
            'avg_response_time': 0
        }
        
        # Get interaction data from interaction_log.db
        interactions = get_interactions(start_date)
        
        if interactions:
            summary['total_interactions'] = len(interactions)
            
            # Summarize sentiment distribution
            for sentiment in ['positive', 'neutral', 'negative']:
                count = sum(1 for i in interactions if i['sentiment'] == sentiment)
                summary['sentiment'][sentiment] = count
            
            # Summarize content type distribution
            content_types = {}
            for interaction in interactions:
                content_type = interaction['content_type']
                content_types[content_type] = content_types.get(content_type, 0) + 1
            summary['content_types'] = content_types
            
            # Calculate average response time
            response_times = []
            for interaction in interactions:
                if interaction.get('mention_timestamp') and interaction.get('timestamp'):
                    try:
                        mention_time = datetime.fromisoformat(interaction['mention_timestamp'].replace('Z', '+00:00'))
                        response_time = datetime.fromisoformat(interaction['timestamp'].replace('Z', '+00:00'))
                        time_diff = (response_time - mention_time).total_seconds()
                        if time_diff >= 0:  # Ensure response time is after mention time
                            response_times.append(time_diff)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid timestamp format for interaction {interaction['tweet_id']}")
            if response_times:
                summary['avg_response_time'] = sum(response_times) / len(response_times) / 60  # Convert to minutes
            else:
                summary['avg_response_time'] = 0
        
        # Get engagement metrics from analytics.db
        metrics = get_metrics(start_date)
        
        if metrics:
            summary['engagement']['total_likes'] = sum(m['likes'] for m in metrics)
            summary['engagement']['total_retweets'] = sum(m['retweets'] for m in metrics)
            summary['engagement']['total_replies'] = sum(m['replies'] for m in metrics)
        
        # Get engagement actions from analytics.db
        engagement_actions = get_engagement_actions(start_date)
        
        if engagement_actions:
            for action in ['like', 'retweet', 'comment']:
                summary['engagement_actions'][action + 's'] = sum(1 for a in engagement_actions if a['action'] == action)
        
        logger.info(f"Generated interaction summary for the past {days} days")
        return summary
    except Exception as e:
        logger.error(f"Error summarizing interactions: {e}")
        return None

def get_interactions(start_date):
    """Get interaction logs since the start date."""
    try:
        conn = sqlite3.connect(INTERACTION_LOG_DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tweet_id, reply_text, sentiment, content_type, timestamp, mention_timestamp
            FROM logs
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (start_date,))
        
        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                'tweet_id': row[0],
                'reply_text': row[1],
                'sentiment': row[2],
                'content_type': row[3],
                'timestamp': row[4],
                'mention_timestamp': row[5]
            })
        
        conn.close()
        return interactions
    except Exception as e:
        logger.error(f"Error retrieving interactions: {e}")
        return []

def get_metrics(start_date):
    """Get engagement metrics since the start date."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT post_id, likes, retweets, replies, timestamp
            FROM metrics
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (start_date,))
        
        metrics = []
        for row in cursor.fetchall():
            metrics.append({
                'post_id': row[0],
                'likes': row[1],
                'retweets': row[2],
                'replies': row[3],
                'timestamp': row[4]
            })
        
        conn.close()
        return metrics
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return []

def get_engagement_actions(start_date):
    """Get engagement actions since the start date."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Ensure engagement table exists (added for resilience)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                tweet_id TEXT,
                action TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (tweet_id, action, timestamp) -- Added to prevent duplicates if re-run
            )
        """)
        conn.commit() # Commit table creation
        
        cursor.execute("""
            SELECT tweet_id, action, timestamp
            FROM engagement
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (start_date,))
        
        actions = []
        for row in cursor.fetchall():
            actions.append({
                'tweet_id': row[0],
                'action': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return actions
    except Exception as e:
        logger.error(f"Error retrieving engagement actions: {e}")
        return []

def store_engagement_action(tweet_id, action):
    """Store an engagement action in analytics.db."""
    try:
        conn = sqlite3.connect(ANALYTICS_DB)
        cursor = conn.cursor()
        
        # Ensure engagement table exists (added for resilience)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement (
                tweet_id TEXT,
                action TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (tweet_id, action, timestamp) -- Added to prevent duplicates if re-run
            )
        """)
        # No need to commit SELECT for table creation check, but will commit after insert
        
        cursor.execute("""
            INSERT INTO engagement (tweet_id, action, timestamp)
            VALUES (?, ?, ?)
        """, (str(tweet_id), action, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored engagement action {action} for tweet {tweet_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing engagement action for tweet {tweet_id}: {e}")
        return False

def log_weekly_summary():
    """Generate and log a weekly summary of interactions and engagement."""
    try:
        summary = summarize_interactions(days=7)
        
        if summary:
            # Generate summary text
            summary_text = f"""
            === WEEKLY SUMMARY: {summary['start_date']} to {summary['end_date']} ===
            Total interactions: {summary['total_interactions']}
            
            Sentiment distribution:
            - Positive: {summary['sentiment']['positive']}
            - Neutral: {summary['sentiment']['neutral']}
            - Negative: {summary['sentiment']['negative']}
            
            Content types:
            {format_content_types(summary['content_types'])}
            
            Engagement received:
            - Likes: {summary['engagement']['total_likes']}
            - Retweets: {summary['engagement']['total_retweets']}
            - Replies: {summary['engagement']['total_replies']}
            
            Engagement actions:
            - Likes given: {summary['engagement_actions']['likes']}
            - Retweets given: {summary['engagement_actions']['retweets']}
            - Comments made: {summary['engagement_actions']['comments']}
            """
            
            logger.info(summary_text)
            return summary_text
        else:
            logger.warning("Failed to generate weekly summary")
            return None
    except Exception as e:
        logger.error(f"Error logging weekly summary: {e}")
        return None

def format_content_types(content_types):
    """Format content types dictionary for display."""
    if not content_types:
        return "None"
    
    formatted = []
    for content_type, count in content_types.items():
        formatted.append(f"- {content_type}: {count}")
    
    return "\n".join(formatted) 