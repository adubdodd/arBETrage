import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
# Format the DataFrame into a readable Discord message
def format_message(df, bet_types=["Home", "Away"], custom_message=None, max_length=2000):
    message = "**🎯 Arbitrage Opportunity Found! 🎯**\n\n"
    messages = []
    
    for _, row in df.iterrows():
        segment = f"📢 **{row['Matchup']}**\n"
        segment += f"🕒 **Start Time:** {row['Start_Time']}\n"

        for bet_type in bet_types:
            bet_key = f"{bet_type}_Bet"
            odds_key = f"{bet_type}_Odds"
            book_key = f"{bet_type}_Bookmaker"

            if bet_key in row and odds_key in row and book_key in row:
                segment += f"🔹 **{bet_type} Bet:** ${row[bet_key]} @ {row[odds_key]} ({row[book_key]})\n"

        segment += f"💰 **Expected Payout:** ${row['Expected_Payout']:.2f}\n"
        segment += f"📈 **Profit:** ${row['Profit']:.2f}\n"

        if custom_message:
            segment += f"📝 {custom_message}\n"

        segment += "--------------------------------------\n"

        # If adding this segment exceeds max_length, store the current message and start a new one
        if len(message) + len(segment) > max_length:
            messages.append(message)
            message = segment  # Start a new message
        else:
            message += segment

    # Append any remaining message
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
