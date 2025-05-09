#!/bin/bash

# setup.sh

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing SQLite databases..."
mkdir -p /tmp
db_files=("pun_library.db" "interaction_log.db" "analytics.db" "model_cache.db")
for db in "${db_files[@]}"; do
    if [ ! -f "/tmp/$db" ]; then
        touch "/tmp/$db"
        echo "Created /tmp/$db"
    else
        echo "/tmp/$db already exists"
    fi
done

echo "Setup complete. Databases initialized in /tmp for Heroku ephemeral filesystem." 