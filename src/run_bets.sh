#!/bin/bash

SPORTS=("baseball" "basketball" "football" "hockey" "soccer")

for SPORT in "${SPORTS[@]}"
do
    if [ "$SPORT" == "soccer" ]; then
        echo "[$(date)] Running soccer bet script..."
        python /src/soccer_bet.py >> /var/log/cron.log 2>&1
    else
        echo "[$(date)] Running two_way_mkt_bet.py for $SPORT..."
        python /src/two_way_mkt_bet.py "$SPORT" >> /var/log/cron.log 2>&1
    fi
done
