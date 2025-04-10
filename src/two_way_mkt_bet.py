import os
import sys
from odds.get_two_way_team import get_odds
from bet_calc.two_way_team import calc_probs, calc_arbitrage
from dotenv import load_dotenv
from notify.discord import format_message, send_to_discord

if __name__ == "__main__":
    load_dotenv()
    if len(sys.argv) < 2:
        SPORT = os.getenv('SPORT')
    else:
        SPORT = sys.argv[1]
    if SPORT not in ['hockey', 'basketball', 'baseball', 'football']:
        print(f"Invalid sport: {SPORT}. Please choose from 'hockey', 'basketball', 'baseball', or 'football'.")
        sys.exit(1)

    with open(f'/src/configs/league_keys/{SPORT}.txt', 'r') as file:
        leagues = file.read().splitlines() 

    odds_df = get_odds(leagues)
    probs_df = calc_probs(odds_df)
    arbitrage_df = calc_arbitrage(probs_df)

    if len(arbitrage_df) > 0:
        print(arbitrage_df.sort_values('Profit', ascending=False).head())
        # notify in discord
        messages = format_message(arbitrage_df, custom_message="Check the odds and place your bets!")
        for message in messages:
            send_to_discord(message)
    else:
        print("No arbitrage opportunities found.")