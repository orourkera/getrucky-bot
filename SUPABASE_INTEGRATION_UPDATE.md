# Supabase Integration Update

This document describes the improvements made to the Supabase integration for the @getrucky Twitter/X bot.

## Issues Addressed

1. **Session ID Access Issue**: There was a discrepancy between session IDs visible in the Supabase UI (up to ID 687) and those accessible via the API (up to ID 647). This caused newer ruck sessions to be inaccessible to the bot.

2. **Map Visualization**: The map generation has been enhanced with better styling, custom markers, and improved session stats display.

3. **Tweet Content**: The tweet content generation has been refined to include more detailed session stats with appropriate emojis.

4. **AI-Powered Observations**: Added XAI-powered observations about ruck sessions to make tweets more insightful and engaging.

## Solutions Implemented

### 1. Direct SQL Query Capability

We've added a direct SQL query capability to bypass API limitations:

- Created `direct_supabase_query.py` which uses Supabase RPC (`exec_sql`) to execute SQL queries directly on the database
- Implemented diagnostic tools to check available session IDs and data
- Updated `post_ruck_session.py` to try standard API first, then fall back to direct SQL queries if the API fails

Usage:
```bash
# Get general database info
python direct_supabase_query.py info

# Get specific session by ID
python direct_supabase_query.py session 684

# Get route points for a session
python direct_supabase_query.py session 684 points

# Get recent sessions
python direct_supabase_query.py recent 10 300

# Run custom SQL query
python direct_supabase_query.py sql "SELECT * FROM ruck_session WHERE id > $1" 680
```

### 2. Enhanced Map Visualization

The map visualization has been improved:

- Added a dark theme for better visual appeal
- Used custom styled markers with informative popups
- Implemented a floating stats box with session details
- Added heat map visualization for route intensity
- Improved styling of the route line (color, weight, dash pattern)

### 3. Improved Tweet Content

Tweet content now includes:

- Location information (city, state, country) when available
- Session stats formatted with appropriate emojis:
  - 🏃‍♂️ Distance in miles
  - ⏱️ Duration
  - 🎒 Ruck weight
  - ⚡ Pace per mile
  - ⛰️ Elevation gain (when significant)

### 4. AI-Powered Observations

The bot now uses XAI to generate insightful observations about ruck sessions:

- Each tweet includes a unique, AI-generated observation about the specific ruck session
- Observations focus on impressive, unusual, or notable aspects of the session
- Examples include comments on pace, endurance, consistency, or challenging terrain
- Keeps observations concise (under 100 characters) to fit within tweet limits
- Falls back to standard messaging if XAI is unavailable

Test the XAI observation feature:
```bash
# Test with XAI-powered observations
python test_specific_session.py --with-xai
```

## Diagnostic Tools

### Session ID Range Checker

The `check_session_id_range.py` script helps diagnose which session IDs are accessible:

```bash
# Check default range (640-690)
python check_session_id_range.py

# Check custom range
python check_session_id_range.py 600 700

# Check with larger step size
python check_session_id_range.py 1 1000 50
```

## Implementation Details

### Direct SQL Query

The direct SQL approach works by using Supabase's RPC capability. This requires creating an RPC function in your Supabase project:

```sql
CREATE OR REPLACE FUNCTION exec_sql(query_text TEXT, params JSONB DEFAULT '[]')
RETURNS JSONB AS $$
DECLARE
  result JSONB;
BEGIN
  EXECUTE query_text USING params INTO result;
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

This function must be created by a Supabase administrator on the database.

### XAI Integration

XAI integration requires:

1. Set the `XAI_API_KEY` environment variable with your xAI/Grok API key
2. Ensure the `api_client.py` module is properly configured to initialize the xAI client
3. For testing, you can use the `GROQ_API_KEY` as a fallback if you don't have an xAI API key

### Usage in Production

For production deployment, we recommend:

1. Set up proper database permissions for the `exec_sql` function
2. Use the standard API first and only fall back to direct SQL as needed
3. Monitor query performance and adjust as necessary
4. Set appropriate rate limits for XAI API calls to avoid exceeding quotas

## Next Steps

1. Implement geocoding to get actual city/state/country information based on coordinates
2. Add more advanced route visualization (elevation profile, speed heatmap)
3. Create a caching mechanism for session data to improve performance
4. Set up monitoring for the session ID discrepancy to understand its root cause
5. Expand the XAI prompts to generate more varied and contextually relevant observations 