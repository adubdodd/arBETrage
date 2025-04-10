#!/bin/bash

# Run the script immediately on container start
# echo "Running initial execution..."
# bash /src/run_bets.sh

# Start cron
echo "Starting cron..."
cron

# Keep the container running and print cron logs
tail -f /var/log/cron.log
