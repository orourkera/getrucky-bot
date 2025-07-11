# AI Marketing Bot Implementation Plan for @getrucky

## Objective
Develop a playful AI marketing bot to promote the rucking app on the @getrucky X account, delivering a diverse mix of pun-heavy content, weekly themes, polls, memes, user shout-outs, and user-generated content (UGC) with a "Ruck it Up" vibe. The bot will leverage xAI's Grok (via API) to generate creative, engaging content, drive user interaction, grow the community, and appeal to casual walkers and hardcore ruckers, deployed on Heroku alongside the rucking app backend. Additionally, the bot will like 90% of posts containing the word "ruck" and retweet posts from valid accounts (e.g., Gary Brecka, Peter Attia, or accounts with >1000 followers).

## Scope
The bot will:
- Post 5-10 times daily with varied content: puns (30%), challenges (20%), weekly themes (20%), polls (10%), memes (10%), user shout-outs (5%), and UGC (5%).
- Interact with posts mentioning @getrucky, delivering witty replies and handling feedback.
- Like 90% of posts containing "ruck" or related terms.
- Retweet posts from valid accounts (e.g., Gary Brecka, Peter Attia, or accounts with >1000 followers) mentioning "ruck."
- Cross-post on accounts mentioning "rucking" with engaging comments.
- Use the rucking app's API to share notable ruck sessions with tailored commentary.

## Implementation Plan

### 1. Requirements Analysis
- **Content Generation**:
  - Create a diverse content library:
    - **Puns**: Rhymes like "Go ruck yourself," "Get Rucky," "Ruck it Up" (30% of posts).
    - **Challenges**: Motivational prompts (e.g., "Ruck 5 miles this weekend!") (20% of posts).
    - **Weekly Themes**: Scheduled themes (e.g., "Ruck Tips Tuesdays" for tips, "Motivation Mondays" for quotes) (20% of posts).
    - **Polls**: Engagement-driven questions (e.g., "What's your ruck weight? 20lb or 40lb?") (10% of posts).
    - **Memes**: Humorous text or image-based content (e.g., "When your ruck feels like a feather 🪶") (10% of posts).
    - **User Shout-outs**: Highlight app users (e.g., "@RuckBoss crushed 10 miles!") (5% of posts).
    - **UGC**: Repost tagged user content (e.g., photos, stories) with credit (5% of posts).
  - Tone: Playful, inclusive, community-driven to attract casual and hardcore ruckers.
  - Use Grok via xAI API to generate dynamic content for each type.
  - Align content with app features (e.g., session tracking, challenges) and brand sass.
- **Interaction**:
  - Reply to @getrucky mentions, replies, and DMs with Grok-generated responses matching content variety (e.g., punny, supportive, or poll-style).
  - Handle feedback based on sentiment:
    - Positive: "Ruck yeah, you're killing it! 🥾 Share your next ruck!"
    - Negative: "Ruck stuck? DM us to keep rolling! 🥾"
    - Neutral: "Got ruck tips? Drop 'em with @getrucky!"
  - Use sentiment analysis for appropriate replies, enhanced by Grok's wit.
- **Engagement**:
  - Like 90% of posts containing "ruck" or related terms (#rucking, #rucklife).
  - Retweet posts mentioning "ruck" from:
    - Specific accounts: Gary Brecka (@GaryBrecka), Peter Attia (@PeterAttiaMD).
    - Any account with >1000 followers (verified via X API user data).
  - Cross-post comments on accounts mentioning "rucking" (e.g., "Ruck 'n' roll with our app!").
- **API Integration**:
  - Fetch ruck session data (distance, duration, location, user stats) via Heroku-hosted app API.
  - Generate posts with Grok-enhanced commentary (e.g., "@RuckStar rucked 10 miles! Join the ruckus! 🥾").

### 2. Technology Stack
- **Platform**: Python for flexibility and API integration.
- **APIs**:
  - X API (v2) for posting, monitoring, liking, retweeting, and replying.
  - Rucking app API (Heroku-hosted) for session data.
  - xAI API (https://x.ai/api) for Grok-based content generation.
- **Sentiment Analysis**: TextBlob for feedback classification (lightweight for Heroku).
- **Scheduling**: APScheduler for automated posting and engagement tasks.
- **Database**: SQLite for content templates, interaction logs, and session data (ephemeral filesystem with backups).
- **Deployment**: Heroku Dynos (Standard-1X) for 24/7 operation, Heroku Postgres for backups.
- **Monitoring**: Heroku Logplex with Papertrail add-on for alerting.
- **Dependencies**:
  - `tweepy`: X API integration.
  - `requests`: App and xAI API calls.
  - `textblob`: Sentiment analysis.
  - `apscheduler`: Scheduling posts and tasks.
  - `psycopg2`: Heroku Postgres backups.

### 3. Development Phases (Checklist)

#### Phase 1: Setup and Configuration (1-2 weeks)
**File: `config.py`**
- [x] Store API credentials using Heroku environment variables:
  - X API: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`.
  - Rucking app API: `APP_API_TOKEN`.
  - xAI API: `XAI_API_KEY`.
- [x] Define constants:
  - `POST_FREQUENCY`: 5-10 posts/day.
  - `SEARCH_TERMS`: `["ruck", "rucking", "#rucking", "#rucklife"]`.
  - `MAX_REPLIES`: 50/hour.
  - `POST_TIMES`: `[8, 10, 12, 15, 18, 21]` (UTC hours).
  - `WEEKLY_THEMES`: `{0: "Motivation Monday", 1: "Ruck Tips Tuesday", 2: "Wellness Wednesday", 3: "Throwback Thursday", 4: "Fitness Friday", 5: "Shout-out Saturday", 6: "Ruck Fun Sunday"}`.
  - `CONTENT_WEIGHTS`: `{pun: 0.3, challenge: 0.2, theme: 0.2, poll: 0.1, meme: 0.1, shoutout: 0.05, ugc: 0.05}`.
  - `LIKE_PROBABILITY`: 0.9 (90% chance to like "ruck" posts).
  - `RETWEET_ACCOUNTS`: `["GaryBrecka", "PeterAttiaMD"]`.
  - `MIN_FOLLOWERS`: 1000 for retweet eligibility.
- [x] Implement `get_config(key)` to safely access environment variables.
- [x] Test configuration loading.

**File: `pun_library.db` (SQLite)**
- [x] Create SQLite database in `/tmp` (Heroku ephemeral filesystem).
- [x] Define schema: `templates (id INTEGER PRIMARY KEY, text TEXT, type TEXT, category TEXT)`.
  - `type`: `"post"`, `"reply"`, `"cross-post"`.
  - `category`: `"pun"`, `"challenge"`, `"theme"`, `"poll"`, `"meme"`, `"shoutout"`, `"ugc"`.
- [x] Populate `pun_library.db` with 100 templates (15-20 per category):
  - Pun: "Ruck it Up with a {distance}-mile sprint! #GetRucky"
  - Challenge: "Can you ruck {distance} miles this week? Tag @getrucky!"
  - Theme: "Ruck Tips Tuesday: Hydrate every {time} minutes! 💧"
  - Poll: "What's your ruck vibe? 🥾 A) Solo B) Squad #GetRucky"
  - Meme: "When your ruck pack feels like a cloud ☁️ #RuckLife"
  - Shout-out: "@RuckStar crushed {distance} miles! 🥾"
  - UGC: "Love this ruck pic from @{user}! Keep rucking! 🥾"
- [x] Implement `insert_template(text, type, category)` and `get_random_template(type, category)` functions.
- [x] Test template retrieval for fallback content.

**File: `api_client.py`**
- [x] X API client (`tweepy`):
  - [x] Authenticate @getrucky with OAuth 1.0a.
  - [x] Function: `post_tweet(text, media=None)`:
    - Post tweet, ensure <280 characters.
    - Support media for memes/UGC (e.g., image URLs).
    - Return tweet ID or raise error.
  - [x] Function: `reply_to_tweet(tweet_id, text, media=None)`:
    - Reply to tweet, include @handle, support media.
    - Return reply ID.
  - [x] Function: `like_tweet(tweet_id)`:
    - Like specified tweet.
    - Return success or raise error.
  - [x] Function: `retweet(tweet_id)`:
    - Retweet specified tweet.
    - Return success or raise error.
  - [x] Function: `search_tweets(query, min_likes=10)`:
    - Search recent tweets for query (e.g., "ruck").
    - Filter for >10 likes for cross-posting.
    - Return tweet objects (include user follower count, media).
  - [x] Function: `get_user_followers(username)`:
    - Fetch follower count for a user.
    - Return integer or raise error.
  - [x] Handle X API rate limits (e.g., 50 tweets/hour, 900 likes/15min) with exponential backoff.
- [x] Rucking app API client (`requests`):
  - [x] Function: `get_ruck_sessions(limit=10, min_distance=5)`:
    - GET request to `https://rucking-app.herokuapp.com/api/sessions`.
    - Parameters: `limit`, `min_distance` (miles).
    - Return JSON: `[{user, distance, duration, location, session_id}, ...]`.
  - [x] Function: `get_session_details(session_id)`:
    - GET request to `https://rucking-app.herokuapp.com/api/sessions/{session_id}`.
    - Return detailed JSON (include user handle, stats).
  - [x] Authenticate with `APP_API_TOKEN` in headers.
  - [x] Handle 429/500 errors with retries.
- [x] xAI API client (`requests`):
  - [x] Function: `generate_text(prompt, max_length=280)`:
    - POST request to xAI API (https://x.ai/api).
    - Payload: `{prompt, max_tokens=100, temperature=0.9}`.
    - Return generated text or raise error.
  - [x] Cache responses in `model_cache.db` to reduce API calls.
  - [x] Handle API rate limits and errors (e.g., 401, 429).
- [x] Test all API functions with mock responses.

**File: `backup.py`**
- [x] Function: `backup_db()`:
  - Copy `pun_library.db`, `interaction_log.db`, `analytics.db`, `model_cache.db` to Heroku Postgres.
  - Schema: `backups (db_name TEXT, data BLOB, timestamp TIMESTAMP)`.
  - Run daily via Heroku Scheduler.
- [x] Function: `restore_db(db_name)`:
  - Restore database from Postgres on dyno restart.
- [x] Test backup/restore process.

**File: `Procfile`**
- [x] Define Heroku process: `web: python main.py`.
- [x] Ensure compatibility with Heroku dyno.

**File: `requirements.txt`**
- [x] List dependencies: `tweepy`, `requests`, `textblob`, `apscheduler`, `psycopg2`.
- [x] Specify versions (e.g., `tweepy==4.14.0`) for stability.

**File: `setup.sh`**
- [x] Script to:
  - Install dependencies: `pip install -r requirements.txt`.
  - Initialize SQLite databases (`pun_library.db`, `interaction_log.db`, `analytics.db`, `model_cache.db`).
  - Populate `pun_library.db` with 100 templates.
- [x] Test via `heroku run bash`.

**Tasks**:
- [x] Obtain API credentials (X, rucking app, xAI).
- [x] Populate `pun_library.db` with 100 templates (15-20 per category).
- [x] Test API connectivity (X, Heroku app API, xAI API). Note: Heroku app API test skipped for now.
- [x] Create Heroku app (`heroku create getrucky-bot`).
- [x] Add Heroku Postgres and Papertrail add-ons.
- [x] Set environment variables (`heroku config:set XAI_API_KEY=xxx`).
- [x] Deploy to Heroku (`git push heroku main`).
- [x] Configure Standard-1X dyno (~$25/month).
- [ ] Enable auto-scaling (1-2 dynos). Note: Skipped for now.
- [x] Set up Papertrail for alerts. Note: Add-on installed; alerts require manual setup via Papertrail dashboard.
- [ ] Schedule daily backups (`backup.py`).

#### Phase 2: Core Functionality (3-4 weeks)
**File: `content_generator.py`**
- [x] Function: `select_content_type()`:
  - Use `CONTENT_WEIGHTS` to randomly select content type (pun, challenge, theme, poll, meme, shoutout, ugc).
  - For themes, check current day for `WEEKLY_THEMES` (e.g., Tuesday → "Ruck Tips Tuesday").
- [x] Function: `generate_post(content_type)`:
  - Prompt xAI API based on type:
    - Pun: "Generate a rucking pun like 'Ruck it Up', <280 characters."
    - Challenge: "Generate a rucking challenge for {distance} miles, <280 characters."
    - Theme: "Generate a {theme} post (e.g., Ruck Tips Tuesday), <280 characters."
    - Poll: "Generate a rucking poll with 2-4 options, <280 characters."
    - Meme: "Generate a humorous rucking meme text, <280 characters."
    - Shout-out: "Generate a shout-out for @{user} rucking {distance} miles, <280 characters."
    - UGC: "Generate a comment for a user's ruck post by @{user}, <280 characters."
  - Example outputs:
    - Pun: "Don't get stuck, ruck! Hit the trail with @getrucky! 🥾"
    - Challenge: "Ruck 3 miles this weekend! Tag @getrucky! #RuckItUp"
    - Theme: "Ruck Tips Tuesday: Stretch before you ruck! 🥾 #GetRucky"
    - Poll: "What's your ruck weight? 🥾 A) 20lb B) 40lb #GetRucky"
    - Meme: "When your ruck feels like a feather 🪶 #RuckLife"
    - Shout-out: "@RuckBoss smashed 8 miles! Ruck on! 🥾"
    - UGC: "Epic ruck pic from @{user}! Keep rucking! 🥾"
  - Cache result in `model_cache.db` (schema: `cache (prompt, response, timestamp)`).
  - Fallback: Random template from `pun_library.db` if API fails.
  - Ensure <280 characters.
- [x] Function: `generate_session_post(xai_headers, session_data)`:
  - Enhanced achievement tracking:
    - Double-digit distance (10+ miles)
    - 100-mile milestone
    - 7-day streak
  - Context-aware prompts with achievements
  - Dynamic emoji selection
  - Enhanced fallback templates
- [x] Function: `generate_reply(xai_headers, tweet_text, sentiment, content_type, sentiment_context)`:
  - Context-aware prompt construction:
    - Sentiment-based tone selection
    - Content type integration
    - Special context handling
  - Enhanced prompt examples:
    - Very positive: "very enthusiastic and encouraging rucking challenge"
    - Very negative: "empathetic and uplifting rucking meme"
    - Question: "informative and helpful rucking theme"
    - Rucking mention: "acknowledging their rucking mention with a shoutout"
  - Dynamic template selection based on sentiment
  - Caching with 24-hour expiration
- [x] Test all functions with mock xAI API responses.

**File: `scheduler.py`**
- [x] Function: `schedule_posts()`:
  - Use APScheduler to schedule 5-10 posts/day.
  - Times: 8 AM, 10 AM, 12 PM, 3 PM, 6 PM, 9 PM (UTC).
  - Generate 3-8 regular posts via `generate_post(select_content_type())`.
  - Generate 2-3 session posts via `generate_session_post()` (fetch sessions from app API).
  - Call `post_tweet()` for each.
- [x] Function: `schedule_engagement()`:
  - Run every 2 hours to search for "ruck" posts.
  - Call `engage_with_posts()` (see `cross_post.py`).
- [x] Function: `start_scheduler()`:
  - Initialize APScheduler with UTC timezone.
  - Handle dyno restarts (persist jobs in memory).
- [x] Test scheduling with dummy posts and engagement tasks.

**File: `interaction_handler.py`**
- [x] Function: `monitor_mentions(x_client, xai_headers)`:
  - Monitor @getrucky mentions every 5 minutes.
  - Process up to `MAX_REPLIES` per hour.
  - Enhanced sentiment analysis with context:
    - Granular sentiment detection (very_positive, positive, neutral, negative, very_negative)
    - Question detection and special handling
    - Rucking mention detection
    - Emoji and hashtag analysis
    - Subjectivity analysis
  - Context-aware reply generation:
    - Dynamic prompt construction based on sentiment and context
    - Special handling for questions and rucking mentions
    - Tone matching for emoji usage
    - Enhanced fallback templates
  - Log interactions with detailed context:
    - Sentiment metrics (polarity, subjectivity)
    - Content characteristics (questions, hashtags, mentions)
    - Interaction metadata (length, emojis, rucking mentions)
- [x] Function: `analyze_sentiment(text)`:
  - Enhanced TextBlob analysis with context:
    - Polarity and subjectivity scores
    - Question detection
    - Hashtag and mention detection
    - Length analysis
    - Rucking keyword detection
    - Emoji presence
  - Return sentiment category and context dictionary
- [x] Function: `select_reply_content_type(sentiment, sentiment_context)`:
  - Dynamic weight adjustment based on sentiment:
    - Very positive: Boost challenges and shoutouts
    - Very negative: Boost memes and puns
    - Questions: Boost themes and challenges
    - Rucking mentions: Boost shoutouts and challenges
  - Normalized weight selection
  - Fallback to puns if no match
- [x] Function: `log_interaction(tweet_id, reply_text, sentiment, content_type, mention_timestamp, sentiment_context)`:
  - Enhanced logging with context:
    - Sentiment metrics
    - Content characteristics
    - Interaction metadata
  - SQLite storage in `/tmp/interaction_log.db`
  - Automatic table creation with new columns
- [x] Test with simulated mentions and replies.

**File: `cross_post.py`**
- [x] Function: `engage_with_posts()`:
  - Query X API every 2 hours for `SEARCH_TERMS`.
  - For each tweet:
    - Like with 90% probability (`LIKE_PROBABILITY`):
      - Call `like_tweet(tweet_id)`.
    - Check retweet eligibility:
      - User in `RETWEET_ACCOUNTS` (e.g., "GaryBrecka") OR `get_user_followers(username) > MIN_FOLLOWERS`.
      - Call `retweet(tweet_id)` if eligible.
    - For cross-posting (limit 10/week):
      - Filter for >10 likes.
      - Prompt xAI API: "Generate a comment for a rucking post, promoting @getrucky, <280 characters."
      - Example: "Rucking fan? Get Rucky with our app! @getrucky 🥾"
      - Cache in `model_cache.db`.
      - Fallback: Use `pun_library.db` cross-post template.
      - Post comment via `reply_to_tweet()`.
  - Log actions in `analytics.db` (schema: `engagement (tweet_id TEXT, action TEXT, timestamp TIMESTAMP)`).
- [x] Test with mock search results and user data.

**File: `tests/test_all.py`**
- [ ] Unit tests for:
  - `api_client.py`: Mock X, app, xAI API responses (include like/retweet).
  - `content_generator.py`: Test Grok-generated posts, replies, session posts across all content types.
  - `interaction_handler.py`: Test sentiment analysis, reply generation with varied content.
  - `scheduler.py`: Test post and engagement scheduling.
  - `cross_post.py`: Test like, retweet, and comment logic.
- [ ] Use `unittest.mock` for API mocks.
- [ ] Run tests via `python -m unittest`.

**Tasks**:
- [x] Implement posting with Grok-generated content (all types).
- [x] Develop interaction handler with sentiment-driven, varied replies.
- [x] Build engagement logic (like 90% of "ruck" posts, retweet valid accounts).
- [x] Test with simulated X posts, app API data, mock xAI API responses.

#### Phase 3: AI Optimization and Deployment (2-3 weeks)
**File: `ai_model.py`**
- [x] Function: `call_xai_api(prompt, max_length=280)`:
  - Send POST request to xAI API (https://x.ai/api).
  - Payload: `{prompt, max_tokens=100, temperature=0.9}` (creative output).
  - Cache response in `model_cache.db` (schema: `cache (prompt, response, timestamp)`).
  - Expire cache entries after 24 hours.
  - Handle errors (401, 429) with retries.
- [x] Function: `get_cached_response(prompt)`:
  - Check `model_cache.db` for recent response.
  - Return cached text or None.
- [x] Test API calls with sample prompts (all content types).
- [x] Monitor xAI API usage to stay within quota.

**File: `moderation.py`**
- [x] Function: `filter_content(text)`:
  - Load blocklist of inappropriate words (stored in `config.py`).
  - Flag text containing blocklist words for manual review.
  - Log flagged content to `analytics.db` (schema: `flags (text, reason, timestamp)`).
- [x] Function: `rate_limit_check(api_type)`:
  - Track X API (50 tweets/hour, 900 likes/15min), xAI API (per quota) usage.
  - Pause operations if nearing limits.
  - Log to Papertrail.
- [x] Test filtering with sample texts.

**File: `analytics.py`**
- [x] Function: `track_engagement()`:
  - Query X API for likes, retweets, replies on @getrucky posts.
  - Store in `analytics.db` (schema: `metrics (post_id TEXT, likes INTEGER, retweets INTEGER, replies INTEGER, timestamp TIMESTAMP)`).
  - Backup to Heroku Postgres.
- [x] Function: `summarize_interactions()`:
  - Aggregate response times, sentiment, content_type from `interaction_log.db`.
  - Summarize like/retweet actions from `engagement`.
  - Calculate average response time, sentiment distribution, engagement rates.
  - Log summary to Papertrail weekly.
- [x] Test with mock X API data.

**File: `main.py`**
- [x] Function: `main()`:
  - Initialize API clients (`api_client.py`).
  - Start scheduler (`scheduler.py`).
  - Start mention monitoring (`interaction_handler.py`).
  - Start engagement loop (`cross_post.py`).
- [x] Error handling:
  - Catch API/model errors, log to Papertrail.
  - Retry failed API calls (max 3 attempts).
  - Restore databases from Postgres on dyno restart.
- [x] Test full bot operation in sandbox.

**Tasks**:
- [ ] Secure xAI API key, test rate limits.
- [x] Implement Grok-based content generation with caching.
- [x] Set up moderation and analytics.
- [x] Deploy to Heroku (`git push heroku main`).
- [ ] Test live for 1 week, monitoring via Papertrail:
  - Verify 5-10 posts/day with varied content.
  - Check mention replies (<1 hour).
  - Confirm likes (90% of "ruck" posts), retweets (valid accounts), and cross-post engagement.

### Additional Deployment Steps
- [x] Create GitHub repository (`https://github.com/orourkera/getrucky-bot.git`)
- [x] Add `.python-version` file to specify Python version for Heroku
- [ ] Set up environment variables on Heroku
- [x] Add Heroku Postgres add-on
- [ ] Install and configure Papertrail for monitoring
- [x] Create schedule for database backups

### Final Tasks
- [x] Create a script to populate `pun_library.db` with 100+ templates (15-20 per category)
- [ ] Set up unit and integration tests
- [ ] Implement a dashboard or reporting mechanism for monitoring bot performance
- [ ] Create a documentation file explaining the bot's features and operation
- [ ] Configure a health check endpoint to verify bot status