import pandas as pd
import requests
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from notify.discord import send_to_discord

from helper_functions import get_legal_sportsbooks

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_odds(leagues: list, raise_on_error: bool = True) -> pd.DataFrame:
    rows = []
    API_KEY = os.getenv('API_KEY')
    STATE = os.getenv('STATE')

    if not API_KEY:
        raise ValueError("Missing API_KEY in environment variables")

    if not STATE:
        raise ValueError("Missing STATE in environment variables")

    for league in leagues:
        try:
            logger.info(f"Requesting odds for league: {league}")

            response = requests.get(
                f'https://api.the-odds-api.com/v4/sports/{league}/odds',
                params={
                    'api_key': API_KEY,
                    'regions': 'us',
                    'markets': 'h2h',
                    'oddsFormat': 'decimal',
                    'dateFormat': 'iso',
                },
                timeout=10  # 10s timeout for faster failover
            )

            if response.status_code == 401:
                logger.warning(response.text)
                send_to_discord('Out of the_odds_API credits')
                break

            if response.status_code != 200:
                logger.warning(f"Failed to get odds for {league}: HTTP {response.status_code} - {response.text}")
                continue

            odds_json = response.json()
            logger.info(f"Retrieved {len(odds_json)} events for league: {league}")  

            for data in odds_json:
                try:
                    match_id = data.get("id")
                    league_title = data.get("sport_title")
                    league_key = data.get("sport_key")
                    start_time = data.get("commence_time")
                    home_team = data.get("home_team")
                    away_team = data.get("away_team")

                    for bookmaker in data.get("bookmakers", []):
                        bookie_name = bookmaker.get("title")
                        row_data = {
                            "Match_ID": match_id,
                            "League_Title": league_title,
                            "League_Key": league_key,
                            "Matchup": f"{home_team} vs. {away_team}",
                            "Start_Time": start_time,
                            "Home_Team": home_team,
                            "Away_Team": away_team,
                            "Bookmaker": bookie_name,
                            "Home_Odds": None,
                            "Away_Odds": None,
                            "Draw_Odds": None
                        }

                        for market in bookmaker.get("markets", []):
                            if market.get("key") != "h2h":
                                continue
                            row_data["Last_Update"] = market.get("last_update")
                            for outcome in market.get("outcomes", []):
                                name = outcome.get("name")
                                price = outcome.get("price")
                                if name == home_team:
                                    row_data["Home_Odds"] = price
                                elif name == away_team:
                                    row_data["Away_Odds"] = price
                                elif name == "Draw":
                                    row_data["Draw_Odds"] = price

                        rows.append(row_data)

                except Exception as e:
                    logger.exception(f"Error processing match data for league {league}: {e}")
                    if raise_on_error:
                        raise

            if league == leagues[-1]:
                logger.info("Remaining API quota: %s", response.headers.get('x-requests-remaining'))
                logger.info("Used API quota: %s", response.headers.get('x-requests-used'))

        except Exception as e:
            logger.exception(f"Error fetching odds for {league}: {e}")
            if raise_on_error:
                raise

    if not rows:
        logger.warning("No odds data returned.")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    logger.info(f'len odds_df: {len(df)}')

    # Filter out illegal bookmakers
    try:
        legal_bookmakers = get_legal_sportsbooks(STATE)
        df = df[df['Bookmaker'].isin(legal_bookmakers)]
        logger.info(f'legal_bm_df len: {len(df)}')
    except Exception as e:
        logger.exception("Error filtering legal sportsbooks")
        if raise_on_error:
            raise

    # Convert and filter by freshness
    try:
        df["Last_Update"] = pd.to_datetime(df["Last_Update"], errors='coerce', utc=True)
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        df = df[df["Last_Update"] >= cutoff_time]
        logger.info(f'len_cutoff df: {len(df)}')
    except Exception as e:
        logger.exception("Error processing Last_Update timestamps")
        if raise_on_error:
            raise

    return df
