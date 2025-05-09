import sqlite3
import os

# Database path (using /tmp for Heroku ephemeral filesystem)
DB_PATH = '/tmp/pun_library.db'

# Templates categorized by type and category
TEMPLATES = {
    'post': {
        'pun': [
            "Ruck it Up with a {distance}-mile trek! 🥾 #GetRucky",
            "Don't get stuck, ruck! Hit {distance} miles today! 🥾 #RuckItUp",
            "Ruck 'n' roll! Smash {distance} miles with @getrucky! 🥾",
            "Get Rucky! Tackle a {distance}-mile ruck today! 🥾 #RuckLife",
            "Ruck yeah! Power through {distance} miles! 🥾 @getrucky",
            "Ruck your world with a {distance}-mile challenge! 🥾 #GetRucky",
            "Don't ruck out, clock {distance} miles! 🥾 #RuckItUp",
            "Ruck on! Crush {distance} miles this week! 🥾 @getrucky",
            "Ruck hard or go home! Aim for {distance} miles! 🥾 #RuckLife",
            "Ruck it out! Push for {distance} miles today! 🥾 #GetRucky",
            "Ruck 'til you drop! Go for {distance} miles! 🥾 @getrucky",
            "Ruck and load! Hit {distance} miles with sass! 🥾 #RuckItUp",
            "Ruck steady! Aim for {distance} miles this weekend! 🥾",
            "Ruck wild! Take on {distance} miles today! 🥾 #GetRucky",
            "Ruck rules! Smash {distance} miles with @getrucky! 🥾",
        ],
        'challenge': [
            "Can you ruck {distance} miles this week? Tag @getrucky! 🥾 #RuckItUp",
            "Challenge: Ruck {distance} miles by Sunday! Show us! 🥾 @getrucky",
            "Ruck {distance} miles this weekend! Who's in? 🥾 #GetRucky",
            "Take on a {distance}-mile ruck! Tag your progress! 🥾 @getrucky",
            "Ruck {distance} miles in 2 days! Can you do it? 🥾 #RuckLife",
            "Push yourself! Ruck {distance} miles this week! 🥾 @getrucky",
            "Ruck challenge: {distance} miles by Friday! Go! 🥾 #GetRucky",
            "Get moving! Ruck {distance} miles and tag us! 🥾 @getrucky",
            "Ruck {distance} miles this month! Track it with us! 🥾 #RuckItUp",
            "Challenge accepted? Ruck {distance} miles! 🥾 @getrucky",
            "Ruck {distance} miles with a buddy! Tag 'em! 🥾 #GetRucky",
            "Aim high! Ruck {distance} miles this week! 🥾 @getrucky",
            "Ruck {distance} miles before the weekend! Go! 🥾 #RuckLife",
            "Step up! Ruck {distance} miles and share! 🥾 @getrucky",
            "Ruck {distance} miles for glory! Tag us! 🥾 #GetRucky",
        ],
        'theme': [
            "Motivation Monday: Ruck {distance} miles to start strong! 🥾 #GetRucky",
            "Ruck Tips Tuesday: Hydrate every {time} minutes! 🥾 #RuckItUp",
            "Wellness Wednesday: Stretch post-ruck for recovery! 🥾 @getrucky",
            "Throwback Thursday: Share your first ruck memory! 🥾 #RuckLife",
            "Fitness Friday: Ruck {distance} miles for gains! 🥾 #GetRucky",
            "Shout-out Saturday: Tag a ruck buddy to crush {distance} miles! 🥾",
            "Ruck Fun Sunday: Enjoy a chill {distance}-mile ruck! 🥾 #RuckItUp",
            "Motivation Monday: You're unstoppable! Ruck {distance} miles! 🥾",
            "Ruck Tips Tuesday: Pack light for a {distance}-mile ruck! 🥾",
            "Wellness Wednesday: Ruck for mental clarity! Try {distance} miles! 🥾",
            "Throwback Thursday: Old ruck gear pic? Share it! 🥾 #GetRucky",
            "Fitness Friday: Power ruck {distance} miles today! 🥾 #RuckLife",
            "Shout-out Saturday: Who's your ruck hero? Tag 'em! 🥾 @getrucky",
            "Ruck Fun Sunday: Scenic {distance}-mile ruck today? Snap it! 🥾",
            "Motivation Monday: Ruck {distance} miles and own the week! 🥾",
        ],
        'poll': [
            "What's your ruck weight? 🥾 A) 20lb B) 40lb #GetRucky",
            "Ruck vibe? 🥾 A) Solo B) Squad #RuckItUp @getrucky",
            "Favorite ruck terrain? 🥾 A) Urban B) Trails #GetRucky",
            "Ruck time? 🥾 A) Morning B) Evening #RuckLife",
            "Ruck goal? 🥾 A) Distance B) Speed #GetRucky @getrucky",
            "Ruck pack style? 🥾 A) Minimal B) Loaded #RuckItUp",
            "Ruck weather? 🥾 A) Sunny B) Rainy #GetRucky",
            "Ruck playlist? 🥾 A) Rock B) Podcasts #RuckLife @getrucky",
            "Ruck distance? 🥾 A) 3 miles B) 10+ miles #GetRucky",
            "Ruck buddy? 🥾 A) Human B) Doggo #RuckItUp @getrucky",
            "Ruck snack? 🥾 A) Energy bar B) Fruit #GetRucky",
            "Ruck challenge? 🥾 A) Hills B) Flat #RuckLife",
            "Ruck gear? 🥾 A) Boots B) Sneakers #GetRucky @getrucky",
            "Ruck pace? 🥾 A) Steady B) Sprint #RuckItUp",
            "Ruck motivation? 🥾 A) Fitness B) Fun #GetRucky",
        ],
        'meme': [
            "When your ruck feels like a feather 🪶 #RuckLife @getrucky",
            "Ruck pack: 40lb. Legs: Priceless. 🥾 #GetRucky",
            "Rucking up hills like a boss! 🥾 #RuckItUp",
            "Ruck now, nap later. 😴 🥾 #RuckLife",
            "When someone says rucking is easy... 😂 🥾 #GetRucky",
            "Ruck pack heavier than my problems! 🥾 #RuckItUp",
            "Rucking: Because walking is too mainstream. 🥾 #RuckLife",
            "Ruck miles > Couch miles. 🥾 #GetRucky @getrucky",
            "When your ruck buddy bails... solo ruck! 🥾 #RuckItUp",
            "Ruck sweat is just weakness leaving! 💪 🥾 #RuckLife",
            "Ruck pack on, world off. 🥾 #GetRucky",
            "Rucking: Turning sidewalks into gains. 🥾 #RuckItUp",
            "When your ruck weight matches your grit! 🥾 #RuckLife",
            "Ruck today, brag tomorrow. 🥾 #GetRucky @getrucky",
            "Rucking: My cardio has weight! 🥾 #RuckItUp",
        ],
        'shoutout': [
            "@RuckStar crushed {distance} miles! Ruck on! 🥾 #GetRucky",
            "Big ruck props to @{user} for {distance} miles! 🥾 #RuckItUp",
            "@{user} smashed {distance} miles! Legend! 🥾 @getrucky",
            "Ruck yeah, @{user}! {distance} miles down! 🥾 #RuckLife",
            "@{user} rucked {distance} miles! Epic! 🥾 #GetRucky",
            "Shout-out to @{user} for {distance} miles! 🥾 #RuckItUp",
            "@{user} owned {distance} miles! Keep rucking! 🥾 @getrucky",
            "Ruck champ @{user} hit {distance} miles! 🥾 #RuckLife",
            "@{user} rucked {distance} miles! Unstoppable! 🥾 #GetRucky",
            "Kudos to @{user} for {distance} miles! 🥾 #RuckItUp @getrucky",
        ],
        'ugc': [
            "Love this ruck pic from @{user}! Keep rucking! 🥾 #GetRucky",
            "Epic ruck moment by @{user}! Share more! 🥾 #RuckItUp",
            "@{user}'s ruck vibe is 🔥! Tag us! 🥾 @getrucky",
            "Ruck inspo from @{user}! Got pics? 🥾 #RuckLife",
            "@{user} showing ruck love! More snaps! 🥾 #GetRucky",
            "Amazing ruck shot by @{user}! Keep it up! 🥾 #RuckItUp",
            "@{user}'s ruck story rocks! Share yours! 🥾 @getrucky",
            "Ruck goals with @{user}'s post! Tag us! 🥾 #RuckLife",
            "@{user} rucking in style! More pics! 🥾 #GetRucky",
            "Cheers to @{user} for this ruck gem! 🥾 #RuckItUp @getrucky",
        ]
    },
    'reply': {
        'pun': [
            "Ruck yeah, you're killing it! Keep rucking! 🥾 #GetRucky",
            "Don't ruck out now, you're on fire! 🥾 #RuckItUp",
            "Ruck 'n' roll! Loving your energy! 🥾 @getrucky",
            "Get Rucky! You're unstoppable! 🥾 #RuckLife",
            "Ruck on, champ! You've got this! 🥾 #GetRucky",
        ],
        'challenge': [
            "Can you ruck {distance} more miles? We believe in you! 🥾 #GetRucky",
            "Challenge: Add {distance} miles this week! Go! 🥾 #RuckItUp",
            "Ruck {distance} miles next! You've got it! 🥾 @getrucky",
            "Push for {distance} miles! Show us! 🥾 #RuckLife",
            "Ruck {distance} miles soon? Tag us! 🥾 #GetRucky",
        ],
        'theme': [
            "Motivation Monday: Keep rucking strong! 🥾 #GetRucky",
            "Ruck Tips Tuesday: Stay hydrated out there! 🥾 #RuckItUp",
            "Wellness Wednesday: Ruck for mind and body! 🥾 @getrucky",
            "Throwback Thursday: Got an old ruck story? 🥾 #RuckLife",
            "Fitness Friday: Ruck hard today! 🥾 #GetRucky",
        ],
        'poll': [
            "Ruck style? 🥾 A) Solo B) Group #GetRucky",
            "Ruck weight? 🥾 A) Light B) Heavy #RuckItUp",
            "Ruck time? 🥾 A) Dawn B) Dusk #RuckLife @getrucky",
            "Ruck goal? 🥾 A) Fun B) Fitness #GetRucky",
            "Ruck terrain? 🥾 A) City B) Wild #RuckItUp",
        ],
        'meme': [
            "Ruck sweat = weakness leaving! 💪 🥾 #GetRucky",
            "Rucking: Cardio with attitude! 🥾 #RuckItUp",
            "Ruck pack heavier than Monday blues! 🥾 #RuckLife",
            "Ruck now, snack later! 😋 🥾 #GetRucky",
            "Rucking: My kind of therapy! 🥾 #RuckItUp @getrucky",
        ],
        'shoutout': [
            "Ruck props to you! Keep crushing it! 🥾 #GetRucky",
            "You're a ruck star! Shine on! 🥾 #RuckItUp",
            "Epic rucking! We're impressed! 🥾 @getrucky",
            "Ruck legend! Keep it up! 🥾 #RuckLife",
            "Ruck champ! You're killing it! 🥾 #GetRucky",
        ],
        'ugc': [
            "Love your ruck content! Share more! 🥾 #GetRucky",
            "Your ruck pics rock! Got more? 🥾 #RuckItUp",
            "Ruck inspo! Keep posting! 🥾 @getrucky",
            "Your ruck story is awesome! More! 🥾 #RuckLife",
            "Ruck vibes! Tag us again! 🥾 #GetRucky",
        ]
    },
    'cross-post': {
        'pun': [
            "Ruck fan? Join the ruckus with @getrucky! 🥾 #GetRucky",
            "Ruck 'n' roll with our app! @getrucky 🥾 #RuckItUp",
            "Get Rucky! Track your rucks with us! 🥾 #RuckLife",
            "Ruck yeah! Join @getrucky for more! 🥾 #GetRucky",
            "Don't ruck alone! Check out @getrucky! 🥾 #RuckItUp",
        ],
        'challenge': [
            "Ruck {distance} miles with @getrucky! Join now! 🥾 #GetRucky",
            "Challenge: Ruck {distance} miles! Track it with @getrucky! 🥾",
            "Can you ruck {distance} miles? Use @getrucky! 🥾 #RuckItUp",
            "Ruck {distance} miles! Log it on @getrucky! 🥾 #RuckLife",
            "Push {distance} miles! Join @getrucky! 🥾 #GetRucky",
        ]
    }
}

def create_database():
    """Create the SQLite database and templates table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")

def insert_template(text, type, category):
    """Insert a single template into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO templates (text, type, category) VALUES (?, ?, ?)", 
                   (text, type, category))
    conn.commit()
    conn.close()

def populate_templates():
    """Populate the database with templates from the TEMPLATES dictionary."""
    create_database()
    count = 0
    for type_key, categories in TEMPLATES.items():
        for category, texts in categories.items():
            for text in texts:
                insert_template(text, type_key, category)
                count += 1
                print(f"Inserted: {text[:50]}... (Type: {type_key}, Category: {category})")
    print(f"Total templates inserted: {count}")

def get_template_count():
    """Get the total number of templates in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM templates")
    count = cursor.fetchone()[0]
    conn.close()
    return count

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # Remove existing DB to avoid duplicates
        print(f"Removed existing database at {DB_PATH}")
    populate_templates()
    total = get_template_count()
    print(f"Database population complete. Total templates: {total}") 