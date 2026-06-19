from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, '/opt/etl')

from pipelines import (
    products, natural_person, services, product_group,
    price_type, inventory_price, producers, legal_entity,
    person_group, workspaces, contracts, return_reason,
)

default_args = {"owner": "yusufjon", "retries": 1}

with DAG(
    dag_id="references_etl",
    description="Smartup — References pipelines",
    default_args=default_args,
    schedule="0 6 * * *",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["smartup", "references"],
) as dag:

    PythonOperator(task_id="products",        python_callable=products.run)
    PythonOperator(task_id="natural_person",  python_callable=natural_person.run)
    PythonOperator(task_id="services",        python_callable=services.run)
    PythonOperator(task_id="product_group",   python_callable=product_group.run)
    PythonOperator(task_id="price_type",      python_callable=price_type.run)
    PythonOperator(task_id="inventory_price", python_callable=inventory_price.run)
    PythonOperator(task_id="producers",       python_callable=producers.run)
    PythonOperator(task_id="legal_entity",    python_callable=legal_entity.run)
    PythonOperator(task_id="person_group",    python_callable=person_group.run)
    PythonOperator(task_id="workspaces",      python_callable=workspaces.run)
    PythonOperator(task_id="contracts",       python_callable=contracts.run)
    PythonOperator(task_id="return_reason",   python_callable=return_reason.run)