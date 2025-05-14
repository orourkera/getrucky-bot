# AI Marketing Bot for @getrucky

An AI-powered marketing bot that promotes the rucking app through engaging content, user interactions, and community engagement on X (formerly Twitter).

## Features

### Content Generation
- Posts 5-10 times daily with varied content:
  - Puns (30%): Playful rucking-related wordplay
  - Challenges (20%): Motivational prompts and goals
  - Weekly Themes (20%): Scheduled content (e.g., "Ruck Tips Tuesday")
  - Polls (10%): Engagement-driven questions
  - Memes (10%): Humorous text-based content
  - User Shout-outs (5%): Highlighting app users
  - UGC (5%): Reposting tagged user content

### Interaction Handling
- Monitors @getrucky mentions every 5 minutes
- Analyzes sentiment and context of interactions
- Generates context-aware replies using xAI
- Logs all interactions for analytics

### Engagement
- Likes 90% of posts containing "ruck" or related terms
- Retweets posts from valid accounts:
  - Specific accounts (Gary Brecka, Peter Attia)
  - Accounts with >1000 followers
- Cross-posts comments on rucking-related content (limit: 10/week)

### Analytics
- Tracks engagement metrics (likes, retweets, replies)
- Monitors response times and sentiment distribution
- Generates weekly performance summaries
- Stores data in SQLite with daily backups to Postgres

### Health Monitoring
- `/health` endpoint for system status
- Monitors database health, API connectivity, and system resources
- Logs issues to Papertrail for alerting

## Setup

### Prerequisites
- Python 3.9+
- Heroku account
- X API credentials
- xAI API key
- Rucking app API token

### Environment Variables
```bash
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret
X_BEARER_TOKEN=your_x_bearer_token
XAI_API_KEY=your_xai_api_key
APP_API_TOKEN=your_app_api_token
DATABASE_URL=your_heroku_postgres_url
```

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/orourkera/getrucky-bot.git
   cd getrucky-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize databases:
   ```bash
   python setup.sh
   ```

### Deployment
1. Create Heroku app:
   ```bash
   heroku create getrucky-bot
   ```

2. Add add-ons:
   ```bash
   heroku addons:create heroku-postgresql:mini
   heroku addons:create papertrail:choklad
   ```

3. Set environment variables:
   ```bash
   heroku config:set X_API_KEY=xxx X_API_SECRET=xxx ...
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

## Development

### Running Tests
```bash
pytest
```

### Code Structure
- `main.py`: Application entry point
- `api_client.py`: API integrations (X, xAI, app)
- `content_generator.py`: Content generation logic
- `interaction_handler.py`: Mention monitoring and replies
- `scheduler.py`: Post and engagement scheduling
- `cross_post.py`: Engagement and cross-posting
- `analytics.py`: Metrics tracking and reporting
- `health.py`: System health monitoring
- `backup.py`: Database backup and restore
- `moderation.py`: Content filtering and rate limiting

### Database Schema
- `pun_library.db`: Content templates
- `interaction_log.db`: Interaction history
- `analytics.db`: Engagement metrics
- `model_cache.db`: Cached AI responses

## Monitoring

### Health Check
Access the health check endpoint:
```
https://getrucky-bot.herokuapp.com/health
```

### Logs
View logs in Papertrail:
```bash
heroku logs --tail -a getrucky-bot
```

### Alerts
Configure Papertrail alerts for:
- Error rates > 1%
- Response times > 5s
- API rate limit warnings
- Database connection issues

## Maintenance

### Backups
- Daily database backups to Postgres
- Manual restore: `python backup.py restore <db_name>`

### Rate Limits
- X API: 50 tweets/hour, 900 likes/15min
- xAI API: Per quota
- Cross-posts: 10/week

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License - see LICENSE file for details 