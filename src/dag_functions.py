import os
import pandas as pd
import logging

from dotenv import load_dotenv
from io import StringIO

from extract.get_two_way_team_odds import get_odds
from extract.get_soccer_odds import get_odds as get_soccer_odds
from transform.bet_calc_two_way_team import calc_probs, calc_arbitrage
from load.mongodb import load_to_mongodb
from notify.discord import format_message, send_to_discord

load_dotenv()

def extract_odds(SPORT:str,**context):
        LEAGUE_FILE = os.getenv('LEAGUE_MAPPING_FILE','') + f'{SPORT}.txt'
        with open(LEAGUE_FILE, 'r') as file:
            leagues = file.read().splitlines()
        logging.info(f'Extracting odds for {len(leagues)} leagues')
        if SPORT == 'soccer':
            odds_df = get_soccer_odds(leagues)
        else:
            odds_df = get_odds(leagues)
        context['ti'].xcom_push(key='odds_df', value=odds_df.to_json())

def check_if_odds_exist(**context):
    odds_json = context['ti'].xcom_pull(key='odds_df')
    odds_df = pd.read_json(StringIO(odds_json))
    return 'transform_odds' if not odds_df.empty else 'end_dag'

def transform_odds(**context):
    odds_df = pd.read_json(StringIO(context['ti'].xcom_pull(key='odds_df')))
    logging.info(f'Calculated probabilities of {len(odds_df)} rows')
    
    probs_df = calc_probs(odds_df)
    logging.info(f'Probabilities df length: {len(probs_df)} rows')
    
    arbitrage_df = calc_arbitrage(probs_df)
    logging.info(f'Arbritrage Opp df length: {len(arbitrage_df)} rows')
    
    context['ti'].xcom_push(key='probs_df', value=probs_df.to_json())
    context['ti'].xcom_push(key='arbitrage_df', value=arbitrage_df.to_json())

def check_if_arbitrage_exists(**context):
    arbitrage_json = context['ti'].xcom_pull(key='arbitrage_df')
    arbitrage_df = pd.read_json(StringIO(arbitrage_json))
    return 'load_to_mongodb' if not arbitrage_df.empty else 'end_dag'

def load_to_mongo(**context):
    logging.info('Loading data to MongoDB')
    
    odds_df = pd.read_json(context['ti'].xcom_pull(key='odds_df'))
    logging.info(f'Odds df length: {len(odds_df)} rows')
    if not odds_df.empty:
        load_to_mongodb(odds_df, db_name='odds', collection_name='odds')
        
    probs_df = pd.read_json(context['ti'].xcom_pull(key='probs_df'))
    logging.info(f'Probabilities df length: {len(probs_df)} rows')
    if not probs_df.empty:
        load_to_mongodb(probs_df, db_name='odds', collection_name='probabilities')
    
    arbitrage_df = pd.read_json(context['ti'].xcom_pull(key='arbitrage_df'))
    logging.info(f'Arbitrage df length: {len(arbitrage_df)} rows')
    if not arbitrage_df.empty:
        load_to_mongodb(arbitrage_df, db_name='odds', collection_name='arbitrage_opportunities')

def notify_discord(**context):
    arbitrage_df = pd.read_json(context['ti'].xcom_pull(key='arbitrage_df'))
    if not arbitrage_df.empty:
        messages = format_message(arbitrage_df.sort_values('Profit', ascending=True), ['Home', 'Away', 'Draw'])
        for message in messages:
            send_to_discord(message)
    else:
        print("No arbitrage opportunities found.")