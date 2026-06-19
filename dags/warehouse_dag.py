from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, '/opt/etl')

from pipelines import (
    cross_movement, internal_movement, stocktaking,
    writeoff, warehouse_input, purchase, logistics,
)

default_args = {"owner": "yusufjon", "retries": 1}

with DAG(
    dag_id="warehouse_etl",
    description="Smartup — Warehouse pipelines",
    default_args=default_args,
    schedule="0 6 * * *",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["smartup", "warehouse"],
) as dag:

    PythonOperator(task_id="cross_movement",    python_callable=cross_movement.run)
    PythonOperator(task_id="internal_movement", python_callable=internal_movement.run)
    PythonOperator(task_id="stocktaking",       python_callable=stocktaking.run)
    PythonOperator(task_id="writeoff",          python_callable=writeoff.run)
    PythonOperator(task_id="warehouse_input",   python_callable=warehouse_input.run)
    PythonOperator(task_id="purchase",          python_callable=purchase.run)
    PythonOperator(task_id="logistics",         python_callable=logistics.run)