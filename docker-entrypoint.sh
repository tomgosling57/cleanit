#!/bin/bash
set -e

echo "Waiting for services to be ready..."
sleep 10

# Populate database if FLASK_ENV is debug or testing
if [ "$FLASK_ENV" = "debug" ] || [ "$FLASK_ENV" = "testing" ]; then
    echo "Populating database for $FLASK_ENV environment..."
    python -c "
import sys
sys.path.append('/app')
from utils.populate_database import populate_database
import os
db_url = os.environ.get('DATABASE_URL')
if db_url:
    try:
        populate_database(db_url)
        print('Database populated successfully')
    except Exception as e:
        print(f'Error populating database: {e}')
else:
    print('DATABASE_URL not set, skipping database initialization')
"
fi

# Choose server based on FLASK_ENV
if [ "$FLASK_ENV" = "debug" ]; then
    echo "Starting Flask development server with auto-reload..."
    exec python app.py --host=0.0.0.0 --port=5000
else
    echo "Starting gunicorn production server..."
    exec gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 app:app
fi