from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta

from dag_functions import (
    extract_odds, 
    check_if_odds_exist, 
    transform_odds, 
    check_if_arbitrage_exists, 
    load_to_mongo, 
    notify_discord
)

SPORT = 'hockey'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='hockey_betting_pipeline',
    default_args=default_args,
    schedule_interval='55 12-23 * * *',
    catchup=False,
    tags=['betting', 'hockey']
) as dag:

    # Define tasks
    t1 = PythonOperator(task_id='extract_odds', python_callable=extract_odds, op_args=[SPORT])
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