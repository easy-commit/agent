#!/bin/bash

APP_FILE="server.py"
APP_MODULE="app"
PORT=5000
WORKERS=4
THREADS=2

if [[ ! -f "$APP_FILE" ]]; then
  echo "❌ File $APP_FILE not found."
  exit 1
fi

if ! command -v gunicorn &> /dev/null; then
  echo "❌ Gunicorn is not installed. Install it with: pip install gunicorn"
  exit 1
fi

echo "🚀 Starting Flask server with Gunicorn..."
echo "📦 Module: ${APP_FILE%.py}:${APP_MODULE} | Port: $PORT | Workers: $WORKERS | Threads: $THREADS"

gunicorn --bind 0.0.0.0:$PORT "${APP_FILE%.py}:${APP_MODULE}" --workers $WORKERS --threads $THREADS
