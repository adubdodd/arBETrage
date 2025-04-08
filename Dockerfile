FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy everything into the container
COPY app/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run a test command (e.g. with "baseball" as the sport argument)
CMD ["python", "two_way_mkt_bet.py", "baseball"]
