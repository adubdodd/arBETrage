import os
from odds.get_soccer import get_odds
from bet_calc.soccer import calc_soccer_probs, calc_arbitrage
from dotenv import load_dotenv
from notify.discord import format_message, send_to_discord

load_dotenv()
SPORT = os.getenv('SPORT')

with open('/src/configs/league_keys/soccer.txt', 'r') as file:
    leagues = file.read().splitlines()

odds_df = get_odds(leagues)

probs_df = calc_soccer_probs(odds_df)

arbitrage_df = calc_arbitrage(probs_df)

if len(arbitrage_df) > 0:
    # notify in discord
    messages = format_message(arbitrage_df.sort_values('Profit', ascending=True), ["Home", "Away", "Draw"], custom_message="Check the odds and place your bets!")
    for message in messages:
        send_to_discord(message)
else:
    print("No arbitrage opportunities found.")