import pandas as pd
import requests
import os
from dotenv import load_dotenv
from helper_functions import get_legal_sportsbooks

load_dotenv()

STATE = os.getenv('STATE','this is not working')
API_KEY = os.getenv('API_KEY')
print(STATE, API_KEY)

def get_odds(leagues:list):
    # List to store rows
    rows = []

    for sport in leagues: 
        API_KEY = os.getenv('API_KEY')
        SPORT = sport
        REGIONS = 'us' # uk | us | eu | au. Multiple can be specified if comma delimited
        MARKETS = 'h2h' # h2h | spreads | totals. Multiple can be specified if comma delimited
        ODDS_FORMAT = 'decimal' # decimal | american
        DATE_FORMAT = 'iso' # iso | unix

        odds_response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
            params={
                'api_key': API_KEY,
                'regions': REGIONS,
                'markets': MARKETS,
                'oddsFormat': ODDS_FORMAT,
                'dateFormat': DATE_FORMAT,
            }
        )

        if odds_response.status_code != 200:
            print(f'Failed to get odds for {sport}: status_code {odds_response.status_code}, response body {odds_response.text}')

        else:
            odds_json = odds_response.json()
            print('Sport:',sport,'  Number of events:', len(odds_json))

        if sport == leagues[-1]:
            # Check the usage quota
            print('Remaining requests:', odds_response.headers['x-requests-remaining'])
            print('Used requests:', odds_response.headers['x-requests-used'])

        for data in odds_json:
            game_id = data["id"]
            sport = data["sport_key"]
            start_time = data["commence_time"]
            home_team = data["home_team"]
            away_team = data["away_team"]

            for bookmaker in data["bookmakers"]:
                bookie_name = bookmaker["title"]
                row_data = {
                    "Game_ID": game_id,
                    "Sport": sport,
                    "Matchup": home_team + ' vs. ' + away_team,
                    "Start_Time": start_time,
                    "Home_Team": home_team,
                    "Away_Team": away_team,
                    "Bookmaker": bookie_name,
                }

                # Extract odds
                for market in bookmaker["markets"]:
                    if market["key"] == "h2h":  # Only process head-to-head odds
                        for outcome in market["outcomes"]:
                            if outcome["name"] == home_team:
                                row_data["Home_Odds"] = outcome["price"]
                            elif outcome["name"] == away_team:
                                row_data["Away_Odds"] = outcome["price"]

                # Append the row
                rows.append(row_data)
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)

    # Filter out bookmakers that are not legal in the state
    legal_bookmakers = get_legal_sportsbooks(STATE)
    df = df[df['Bookmaker'].isin(legal_bookmakers)]
    return df