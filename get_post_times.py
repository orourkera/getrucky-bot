import random
from datetime import datetime
from zoneinfo import ZoneInfo

from config import get_post_times

# Get today's post times
post_times = get_post_times()

# Define time zones
UTC = ZoneInfo("UTC")
CEST = ZoneInfo("Europe/Paris")

print("Scheduled post times for today:")
for hour, minute in post_times:
    # Create a datetime object for today at the specified hour and minute in UTC
    now = datetime.now(UTC)
    post_time_utc = datetime(now.year, now.month, now.day, hour, minute, tzinfo=UTC)
    
    # Convert to CEST
    post_time_cest = post_time_utc.astimezone(CEST)
    
    print(f"- UTC: {post_time_utc.strftime('%H:%M')} | CEST: {post_time_cest.strftime('%H:%M')}") 