#!/bin/bash

while true
do
  echo "🔁 Starting EasyCommit..."
  python3 train_model.py
  echo "⚠️ Script crashed. Restarting in 5 seconds..."
  sleep 5
done
