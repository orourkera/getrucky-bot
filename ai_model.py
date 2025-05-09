# ai_model.py

import time
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from config import XAI_API_KEY

logger = logging.getLogger(__name__)

# Database path
MODEL_CACHE_DB = '/tmp/model_cache.db'

def call_xai_api(prompt, max_length=280, temperature=0.9, max_retries=3):
    """Send a request to xAI API with retries and caching."""
    # Check cache first
    cached_response = get_cached_response(prompt)
    if cached_response:
        logger.info(f"Using cached response for prompt: {prompt[:30]}...")
        return cached_response
    
    # Prepare API request
    headers = {
        'Authorization': f'Bearer {XAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'prompt': prompt,
        'max_tokens': 100,
        'temperature': temperature
    }
    
    # Try API call with retries
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://x.ai/api",
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            # Extract and format text
            generated_text = response.json().get('choices', [{}])[0].get('text', '').strip()
            if len(generated_text) > max_length:
                generated_text = generated_text[:max_length-3] + '...'
            
            # Cache successful response
            if generated_text:
                cache_response(prompt, generated_text)
                logger.info(f"Generated and cached text for prompt: {prompt[:30]}...")
                return generated_text
            else:
                logger.warning(f"xAI API returned empty response for prompt: {prompt[:30]}")
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            
            if status_code == 401:
                logger.error("API authentication error (401). Check API key.")
                break  # Don't retry auth errors
                
            elif status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit reached (429). Waiting {retry_after} seconds before retry.")
                time.sleep(retry_after)
                
            else:
                logger.error(f"HTTP error during API call: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during API call: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to generate text after {max_retries} attempts for prompt: {prompt[:30]}")
    return None

def get_cached_response(prompt):
    """Retrieve a cached response for the given prompt, if not expired."""
    try:
        conn = sqlite3.connect(MODEL_CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT response, timestamp FROM cache WHERE prompt = ?",
            (prompt,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
            
        response, timestamp_str = result
        timestamp = datetime.fromisoformat(timestamp_str)
        
        # Check if cache entry is still valid (less than 24 hours old)
        if datetime.utcnow() - timestamp < timedelta(hours=24):
            logger.info(f"Cache hit for prompt: {prompt[:30]}...")
            return response
        else:
            logger.info(f"Cache expired for prompt: {prompt[:30]}...")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving cached response: {e}")
        return None

def cache_response(prompt, response):
    """Cache a generated response with a timestamp."""
    try:
        conn = sqlite3.connect(MODEL_CACHE_DB)
        cursor = conn.cursor()
        
        # Ensure the cache table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                prompt TEXT PRIMARY KEY,
                response TEXT,
                timestamp TEXT
            )
        """)
        
        # Store the current timestamp in ISO format for easy comparison
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute(
            "INSERT OR REPLACE INTO cache (prompt, response, timestamp) VALUES (?, ?, ?)",
            (prompt, response, timestamp)
        )
        conn.commit()
        conn.close()
        logger.info(f"Cached response for prompt: {prompt[:30]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error caching response: {e}")
        return False

def clear_expired_cache_entries():
    """Clear cache entries older than 24 hours."""
    try:
        conn = sqlite3.connect(MODEL_CACHE_DB)
        cursor = conn.cursor()
        
        # Calculate the cutoff timestamp (24 hours ago)
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        # Delete expired entries
        cursor.execute(
            "DELETE FROM cache WHERE timestamp < ?",
            (cutoff_time,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} expired cache entries")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error clearing expired cache entries: {e}")
        return 0

def get_api_usage_stats():
    """Get statistics on API usage based on cached entries."""
    try:
        conn = sqlite3.connect(MODEL_CACHE_DB)
        cursor = conn.cursor()
        
        # Count total cache entries
        cursor.execute("SELECT COUNT(*) FROM cache")
        total_entries = cursor.fetchone()[0]
        
        # Count entries from last 24 hours
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM cache WHERE timestamp > ?", (cutoff_time,))
        recent_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_cached": total_entries,
            "cached_last_24h": recent_entries,
            "estimated_api_calls_saved": total_entries
        }
        
    except Exception as e:
        logger.error(f"Error retrieving API usage stats: {e}")
        return {
            "total_cached": 0,
            "cached_last_24h": 0,
            "estimated_api_calls_saved": 0
        } 