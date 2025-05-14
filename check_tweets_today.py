import sqlite3
from datetime import datetime, timedelta

DB_PATH = '/tmp/interaction_log.db'

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    since = (datetime.utcnow() - timedelta(days=1)).isoformat()
    cursor.execute('SELECT tweet_id, timestamp FROM logs WHERE timestamp > ?', (since,))
    rows = cursor.fetchall()
    if rows:
        print('Tweets posted in the last 24 hours:')
        for tweet_id, timestamp in rows:
            print(f'- Tweet ID: {tweet_id}, Timestamp: {timestamp}')
    else:
        print('No tweets posted in the last 24 hours.')
    conn.close()
except Exception as e:
    print(f'Error checking tweets: {e}') 