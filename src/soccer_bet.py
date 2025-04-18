import os
from extract.get_soccer_odds import get_odds
from transform.bet_calc_soccer import calc_soccer_probs, calc_arbitrage
from load.mongodb import load_to_mongodb
from dotenv import load_dotenv
from notify.discord import format_message, send_to_discord

load_dotenv()
SPORT = os.getenv('SPORT')

with open('/src/configs/league_keys/soccer.txt', 'r') as file:
    leagues = file.read().splitlines()

# Extract
odds_df = get_odds(leagues)
# Tranform
probs_df = calc_soccer_probs(odds_df)
arbitrage_df = calc_arbitrage(probs_df)
# Load
load_to_mongodb(odds_df), db_name=''
load_to_mongodb()
load_to_mongodb(arbitrage_df,)

# Notify
if len(arbitrage_df) > 0:
    # notify in discord
    messages = format_message(arbitrage_df.sort_values('Profit', ascending=True), ['Home', 'Away', 'Draw'])
    for message in messages:
        send_to_discord(message)
else:
    print('No arbitrage opportunities found.')