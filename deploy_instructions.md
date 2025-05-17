# Deployment Instructions for Supabase Integration

Follow these steps to deploy the Supabase integration to your Heroku app:

## 1. Set Environment Variables

Add the Supabase credentials to your Heroku app:

```bash
heroku config:set SUPABASE_URL=https://zmxapklvrbafuwhkefhf.supabase.co
heroku config:set SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpteGFwa2x2cmJhZnV3aGtlZmhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyMTk5MjAsImV4cCI6MjA1OTc5NTkyMH0.9S9zUDHZmTA42_eojPfcYdXyTwm6cVCOyUj0UerNxeo
```

## 2. Update Dependencies

The Supabase integration requires additional dependencies. Add them to your Heroku app:

```bash
git add requirements.txt
git commit -m "Add Supabase and map generation dependencies"
git push heroku main
```

## 3. Deploy the Changes

Push all your changes to Heroku:

```bash
git add supabase_client.py content_generator.py scheduler.py
git commit -m "Add Supabase integration and map post functionality"
git push heroku main
```

## 4. Test the Integration

Test the ruck session post functionality:

```bash
# Test locally
python post_ruck_session.py

# Or on Heroku
heroku run python post_ruck_session.py
```

## 5. Troubleshooting

If you encounter any issues, check the logs:

```bash
heroku logs --tail
```

Common issues:
- Missing environment variables
- Database connectivity issues
- API rate limits

## 6. Next Steps

- Consider adding image generation capabilities for maps
- Set up a schedule for map posts 
- Monitor engagement on map posts

## 7. Update README

Update your project README to document the new functionality:

```markdown
## Map Post Feature

The bot can now generate and post ruck session data from Supabase, showing:
- Distance
- Duration
- Pace
- Weight carried
- Elevation gain

In future updates, actual route maps will be included in the posts.
``` 