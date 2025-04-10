import requests
import os
import pandas as pd
from dotenv import load_dotenv

from notify.url_builder import build_sportsbook_url
from helper_functions import decimal_to_american

load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
# Format the DataFrame into a readable Discord message
def format_message(df, bet_types=["Home", "Away"], custom_message=None, max_length=2000):
    message = "**🎯 @here Arbitrage Opp. Found! 🎯**\n\n"
    messages = []

    for _, row in df.iterrows():
        segment = f"📢 **{row['Matchup']}**\n"
        segment += f"🕒 **Start Time:** {row['Start_Time']}\n"

        league = row.get("League", "unknown_league")  # You need a League column in your df

        for bet_type in bet_types:
            bet_key = f"{bet_type}_Bet"
            odds_key = f"{bet_type}_Odds"
            book_key = f"{bet_type}_Bookmaker"

            if bet_key in row and odds_key in row and book_key in row:
                bookmaker = row[book_key]
                url = build_sportsbook_url(bookmaker, league)
                if "Error" in url:
                    link_text = f"${row[bet_key]} @ {decimal_to_american(row[odds_key])} ({bookmaker})"
                else:
                    link_text = f"[${row[bet_key]} @ {decimal_to_american(row[odds_key])}]({'<'+url+'>'}) ({bookmaker})"

                segment += f"🔹 **{bet_type} Bet:** {link_text}\n"

        segment += f"💰 **Expected Payout:** ${row['Expected_Payout']:.2f}\n"
        segment += f"📈 **Profit:** ${row['Profit']:.2f}\n"

        if custom_message:
            segment += f"📝 {custom_message}\n"

        segment += "--------------------------------------\n"

        if len(message) + len(segment) > max_length:
            messages.append(message)
            message = segment
        else:
            message += segment

    if message:
        messages.append(message)

    return messages


# Send the message to Discord
def send_to_discord(message):
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK, json=payload)
    
    if response.status_code == 204:
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Error sending message: {response.status_code}, {response.text}")
