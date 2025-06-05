#!/usr/bin/env bash
set -e

VENV_ACTIVATE="source /app/venv/bin/activate"

kill_sessions() {
  echo "🛑 Killing existing tmux sessions..."
  tmux kill-session -t server 2>/dev/null || true
  tmux kill-session -t train 2>/dev/null || true
}

start_sessions() {
  echo "🚀 Starting tmux sessions..."
  tmux start-server

  tmux has-session -t server 2>/dev/null || \
    tmux new-session -d -s server "$VENV_ACTIVATE && gunicorn server:app --bind 0.0.0.0:5000 --workers 4 --threads 2"

  tmux has-session -t train 2>/dev/null || \
    tmux new-session -d -s train "$VENV_ACTIVATE && python train_model.py"

  echo "✅ Sessions launched: [server, train]"
}

restart_sessions() {
  kill_sessions
  sleep 1
  start_sessions
}

case "$1" in
  start)
    echo "🔍 TRAIN_ON_START: $TRAIN_ON_START"
    if [ "$TRAIN_ON_START" = "true" ]; then
      start_sessions
    else
      echo "⚠️  TRAIN_ON_START is not set to true. Skipping auto start."
    fi
    ;;
  restart)
    restart_sessions
    ;;
  kill)
    kill_sessions
    ;;
  *)
    echo "🔧 Usage: ./start.sh [start|restart|kill]"
    echo "💤 Defaulting to idle mode..."
    ;;
esac

tail -f /dev/null
