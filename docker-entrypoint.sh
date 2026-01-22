#!/bin/bash
set -e

echo "Waiting for services to be ready..."
sleep 10

# Create S3 bucket if it doesn't exist (for MinIO)
if [ "$STORAGE_PROVIDER" = "s3" ]; then
    echo "Checking S3 bucket configuration..."
    python -c "
import sys
sys.path.append('/app')
import os
from libcloud.storage.types import Provider
from libcloud.storage.providers import get_driver
from urllib.parse import urlparse

access_key = os.environ.get('AWS_ACCESS_KEY_ID', os.environ.get('MINIO_ROOT_USER', 'minioadmin'))
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin'))
endpoint = os.environ.get('S3_ENDPOINT_URL', 'http://minio:9000')
bucket = os.environ.get('S3_BUCKET', 'cleanit-media')

print(f'Configuring S3 bucket: {bucket}')

try:
    cls = get_driver(Provider.S3)
    parsed = urlparse(endpoint)
    
    driver_args = {
        'key': access_key,
        'secret': secret_key,
        'region': os.environ.get('AWS_REGION', 'us-east-1'),
        'host': parsed.hostname,
        'port': parsed.port,
        'secure': parsed.scheme == 'https',
    }
    
    driver = cls(**driver_args)
    
    # Check if bucket exists
    try:
        container = driver.get_container(bucket)
        print(f'✓ Bucket \"{bucket}\" already exists')
    except Exception:
        # Create bucket if it doesn't exist
        container = driver.create_container(bucket)
        print(f'✓ Created bucket \"{bucket}\"')
        
except Exception as e:
    print(f'✗ Error configuring S3 bucket: {e}')
    import traceback
    traceback.print_exc()
"
fi

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
        populate_database(db_url, False)
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