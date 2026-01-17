#!/bin/bash
# Startup script for production deployment

set -e

echo "=========================================="
echo "Starting AI Assistant Backend"
echo "=========================================="

# Wait for database to be ready
echo "Waiting for database to be ready..."
python -c "
import time
import sys
from sqlalchemy import create_engine, text
from app.config import settings

max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready!')
        engine.dispose()
        sys.exit(0)
    except Exception as e:
        print(f'Attempt {i+1}/{max_retries}: Database not ready yet... ({e})')
        time.sleep(retry_interval)

print('Database connection failed after maximum retries')
sys.exit(1)
"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
