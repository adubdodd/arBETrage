# Sports Betting Recommender Engine Plan

## 1. Data Collection (Real-time Arbitrage Detection)
- **Integrate with the Odd-API** to pull real-time odds for Premier League matches.
- Identify and store relevant odds (match outcome, over/under, etc.) for arbitrage detection.

## 2. Arbitrage and Postitive Expected Value Detection Logic
- **Develop an algorithm** to identify arbitrage opportunities by comparing odds from multiple bookmakers.
- Programatcally calculate **fair odds** and develop an algorithm to compare odds from bookmaker looking for **positive EV** odds.
- Use **thresholds** to trigger alerts for profitable arbitrage opportunities.



## 3. Logging System
- Implement a **logging system** to track detected arbitrage opportunities.
- Log key details, including:
  - Timestamp
  - Odds from different bookmakers
  - Profit margin
  - Time of detection
- Store logs in a simple format (e.g., JSON, CSV) for easy analysis.

## 4. Alerts
- Set up **messaging alerts** via Discord or Telegram for detected opportunities.
- Include a summary of the arbitrage opportunity in the alert message.

## 5. Dashboard
- Build a simple **dashboard** to display real-time odds and arbitrage opportunities.
- Display stats like:
  - Matched odds
  - Profit margin
  - Time of detection
- Keep the dashboard simple at first, focusing on functionality.

## 6. Local Deployment
- Run the system **locally** to iterate and test.
- Set up a local database (SQLite or a file-based database) for storing odds and arbitrage history.

## 7. Move to AWS
- Set up AWS infrastructure using:
  - **Lambda** for event-driven processing
  - **DynamoDB** or **RDS** for storage
  - **EC2/ECS** for hosting the dashboard
- Migrate your data and ensure scalability as the system grows.

## 8. Expand to Historical Data
- Once the real-time system is stable, consider subscribing to a paid API for **historical odds**.
- Implement backtesting or trend analysis using historical data.
