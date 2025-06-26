import pandas as pd
import requests
import os
import logging

from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

from helper_functions import get_legal_sportsbooks
from notify.discord import send_to_discord

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_odds(leagues:list) -> pd.DataFrame:
    # List to store rows
    rows = []
    API_KEY = os.getenv('API_KEY')
    STATE = os.getenv('STATE')

    if not API_KEY:
        raise ValueError("Missing API_KEY in environment variables")
    logger.info(f"API_KEY:{API_KEY}")

    if not STATE:
        raise ValueError("Missing STATE in environment variables")
    logger.info(f"State:{STATE}")

    for league in leagues:
        try:
            logger.info(f"Requesting odds for league: {league}") 

            SPORT = league
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


            if odds_response.status_code == 401:
                logger.warning(odds_response.text['message'])
                send_to_discord('Out of the_odds_API credits')
                break

            if odds_response.status_code != 200:
                logger.warning(f"Failed to get odds for {league}: HTTP {odds_response.status_code} - {odds_response.text}")
                continue
    
            odds_json = odds_response.json()
            logger.info(f"Retrieved {len(odds_json)} events for league: {league}")

            for data in odds_json:
                try:
                    game_id = data["id"]
                    league_title = data["sport_title"]
                    league_key = data["sport_key"]
                    start_time = data["commence_time"]
                    home_team = data["home_team"]
                    away_team = data["away_team"]

                    for bookmaker in data["bookmakers"]:
                        bookie_name = bookmaker["title"]
                        row_data = {
                            "Game_ID": game_id,
                            "League_Title": league_title,
                            "League_Key": league_key,
                            "Matchup": home_team + ' vs. ' + away_team,
                            "Start_Time": start_time,
                            "Home_Team": home_team,
                            "Away_Team": away_team,
                            "Bookmaker": bookie_name,
                        }

                        # Extract odds
                        for market in bookmaker["markets"]:
                            row_data["Last_Update"] = market["last_update"]
                            if market["key"] == "h2h":  # Only process head-to-head odds
                                for outcome in market["outcomes"]:
                                    if outcome["name"] == home_team:
                                        row_data["Home_Odds"] = outcome["price"]
                                    elif outcome["name"] == away_team:
                                        row_data["Away_Odds"] = outcome["price"]

                        rows.append(row_data)

                except Exception as e:
                    logger.exception(f'Error processing match data for league {league}: {e}')
                    raise e

            if league == leagues[-1]:
                # Check the usage quota
                print('Remaining requests:', odds_response.headers['x-requests-remaining'])
                print('Used requests:', odds_response.headers['x-requests-used'])
            
        except Exception as e:
            logger.exception("Error fetching odds for {league}: e")
            raise e
    
    if not rows:
        logger.warning("No odds data returned")
        return pd.DataFrame()
    
    df = pd.DataFrame(rows)
    logger.info(f'len odds_df: {len(df)}')

    # Filter out bookmakers that are not legal in the state
    try:
        legal_bookmakers = get_legal_sportsbooks(STATE)
        df = df[df['Bookmaker'].isin(legal_bookmakers)]
        logger.info(f'legal_bm_df len: {len(df)}')
    except Exception as e:
        logger.exception("Error filtering legal sportsbooks")
        raise e

    # Cutoff time
    try:
        df["Last_Update"] = pd.to_datetime(df["Last_Update"], errors='coerce', utc=True)
        # Define freshness threshold in UTC
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        df = df[df["Last_Update"] >= cutoff_time]
        logger.info(f'len_cutoff df: {len(df)}')
    except Exception as e:
        logger.exception("Error processing Last_Update timestamps")
        raise e
    
    return df