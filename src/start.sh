#!/bin/bash

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
until nc -z mongo 27017; do
  echo "Mongo is unavailable - sleeping"
  sleep 2
done

echo "Mongo is up - continuing"

# Optionally run the initial script
# echo "Running initial execution..."
# bash /src/run_bets.sh

# Start cron
echo "Starting cron..."
cron

# Keep the container running and print cron logs
tail -f /var/log/cron.log