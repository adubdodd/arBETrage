#!/bin/bash

# Add PATH manually for cron
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

PYTHON=/usr/local/bin/python  # or use output from `which python`

SPORTS=("baseball" "basketball" "football" "hockey" "soccer")

for SPORT in "${SPORTS[@]}"
do
    if [ "$SPORT" == "soccer" ]; then
        echo "[$(date)] Running soccer_bet.py for $SPORT..."
        $PYTHON /src/soccer_bet.py >> /var/log/cron.log 2>&1
    else
        echo "[$(date)] Running two_way_mkt_bet.py for $SPORT..."
        $PYTHON /src/two_way_mkt_bet.py "$SPORT" >> /var/log/cron.log 2>&1
    fi
done