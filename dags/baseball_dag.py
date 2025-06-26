from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
from dotenv import load_dotenv
from io import StringIO
import os

from extract.get_two_way_team_odds import get_odds
from transform.bet_calc_two_way_team import calc_probs, calc_arbitrage
from load.mongodb import load_to_mongodb
from notify.discord import format_message, send_to_discord

import pandas as pd

load_dotenv()
SPORT = os.getenv('SPORT', 'baseball')
LEAGUE_FILE = '/opt/airflow/src/configs/league_keys/baseball.txt'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='baseball_betting_pipeline',
    default_args=default_args,
    schedule_interval='55 12-23 * * *',
    catchup=False,
    tags=['betting', 'baseball']
) as dag:

    def extract_odds(**context):
        with open(LEAGUE_FILE, 'r') as file:
            leagues = file.read().splitlines()
        odds_df = get_odds(leagues)
        context['ti'].xcom_push(key='odds_df', value=odds_df.to_json())

    def check_if_odds_exist(**context):
        odds_json = context['ti'].xcom_pull(key='odds_df')
        odds_df = pd.read_json(StringIO(odds_json))
        return 'transform_odds' if not odds_df.empty else 'end_dag'

    def transform_odds(**context):
        odds_df = pd.read_json(StringIO(context['ti'].xcom_pull(key='odds_df')))
        probs_df = calc_probs(odds_df)
        arbitrage_df = calc_arbitrage(probs_df)
        context['ti'].xcom_push(key='probs_df', value=probs_df.to_json())
        context['ti'].xcom_push(key='arbitrage_df', value=arbitrage_df.to_json())

    def check_if_arbitrage_exists(**context):
        arbitrage_json = context['ti'].xcom_pull(key='arbitrage_df')
        arbitrage_df = pd.read_json(StringIO(arbitrage_json))
        return 'load_to_mongodb' if not arbitrage_df.empty else 'end_dag'

    def load_to_mongo(**context):
        odds_df = pd.read_json(context['ti'].xcom_pull(key='odds_df'))
        probs_df = pd.read_json(context['ti'].xcom_pull(key='probs_df'))
        arbitrage_df = pd.read_json(context['ti'].xcom_pull(key='arbitrage_df'))

        load_to_mongodb(odds_df, db_name='odds', collection_name='odds')
        load_to_mongodb(probs_df, db_name='odds', collection_name='probabilities')
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

    t1 = PythonOperator(task_id='extract_odds', python_callable=extract_odds)
    t2 = BranchPythonOperator(task_id='check_if_odds_exist', python_callable=check_if_odds_exist)
    t3 = PythonOperator(task_id='transform_odds', python_callable=transform_odds)
    t4 = BranchPythonOperator(task_id='check_if_arbitrage_exists', python_callable=check_if_arbitrage_exists)
    t5 = PythonOperator(task_id='load_to_mongodb', python_callable=load_to_mongo)
    t6 = PythonOperator(task_id='notify_discord', python_callable=notify_discord)
    end = DummyOperator(task_id='end_dag')

    # DAG flow
    t1 >> t2
    t2 >> t3 >> t4
    t2 >> end
    t4 >> t5 >> t6
    t4 >> end
