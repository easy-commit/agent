#!/bin/bash

set -e

if [[ -f "venv/bin/activate" ]]; then
  echo "📦 Activating virtual environment..."
  source venv/bin/activate
else
  echo "❌ Virtual environment not found in ./venv"
  exit 1
fi

echo "🚀 Starting model training..."
python3 train_model.py | tee logs/train_$(date +%F_%H-%M-%S).log

