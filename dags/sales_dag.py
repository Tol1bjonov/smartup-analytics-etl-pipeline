from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, '/opt/etl')

from pipelines import order, returns, visit

default_args = {"owner": "yusufjon", "retries": 1}

with DAG(
    dag_id="sales_etl",
    description="Smartup — Sales pipelines",
    default_args=default_args,
    schedule="0 6 * * *",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["smartup", "sales"],
) as dag:

    PythonOperator(task_id="order",   python_callable=order.run)
    PythonOperator(task_id="returns", python_callable=returns.run)
    PythonOperator(task_id="visit",   python_callable=visit.run)