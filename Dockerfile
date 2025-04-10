FROM python:3.11-slim

ENV TZ=America/New_York

RUN apt-get update && \
    apt-get install -y cron tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY src/ /src/
COPY src/start.sh /src/start.sh
COPY cronjob /etc/cron.d/cronjob
COPY .env /src/.env

RUN chmod 0644 /etc/cron.d/cronjob && crontab /etc/cron.d/cronjob
RUN chmod +x /src/start.sh
RUN chmod +x /src/run_bets.sh
RUN pip install --no-cache-dir -r requirements.txt

RUN touch /var/log/cron.log


CMD ["/src/start.sh"]