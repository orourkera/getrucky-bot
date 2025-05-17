# Supabase Integration for @getrucky Bot

This document explains how the @getrucky Twitter bot integrates with Supabase to fetch and post ruck session data.

## Overview

The bot now connects to your Supabase database to fetch ruck session data and generate tweets showing:

- Distance in miles
- Duration
- Pace (min/mile)
- Weight carried (kg)
- Elevation gain (m)

This provides real-world rucking data to your Twitter followers, making your content more authentic and engaging.

## Database Schema

The integration uses the following tables:

1. **ruck_session**: Contains data about individual ruck sessions
   - Key fields: id, user_id, distance_km, duration_seconds, ruck_weight_kg, etc.

2. **location_point**: Contains GPS coordinates for route mapping
   - Key fields: id, session_id, latitude, longitude

## Implementation Details

### Files

- **supabase_client.py**: Core integration with Supabase
- **content_generator.py**: Generates tweet text from session data
- **scheduler.py**: Handles scheduling of map posts
- **post_ruck_session.py**: Manual script to post a ruck session

### Key Functions

1. **get_recent_ruck_sessions**: Fetches recent sessions from Supabase
2. **get_session_route_points**: Gets route points for mapping
3. **format_session_data**: Processes raw database data for display
4. **generate_map_post_text**: Creates engaging tweet text

## Data Flow

1. Bot connects to Supabase using API credentials
2. Fetches recent ruck session data
3. Formats distances (km to miles), calculates pace
4. Generates tweet text with session highlights
5. Posts to Twitter with properly formatted content

## Future Enhancements

1. **Actual Map Images**: Convert route coordinates to shareable maps
2. **More Session Metrics**: Include heart rate, cadence, energy expenditure
3. **Achievements**: Highlight milestones, streaks, PRs
4. **User Tagging**: Optional tagging of users who completed sessions (with permission)

## Security Considerations

- The integration uses the "anon" API key with limited permissions
- No personally identifiable information is shared without consent
- App adheres to Twitter's content policies

## Testing and Monitoring

Run tests using these scripts:
- `test_supabase_connection.py`: Verify database connectivity
- `test_map_post.py`: Test tweet generation without posting
- `post_ruck_session.py`: Post a real tweet (requires confirmation)

## Troubleshooting

Common issues:
1. **No data available**: Check database has entries in the ruck_session table
2. **Column errors**: Verify column names match expected schema
3. **Authentication errors**: Confirm Supabase URL and key are correctly set 