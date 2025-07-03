from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import requests
from io import StringIO
import logging

default_args = {
    'owner': 'Sergey',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

S3_URL = "https://9c579ca6-fee2-41d7-9396-601da1103a3b.selstorage.ru/credit_clients.csv"

def update_clients_from_s3():
    # 1. Скачиваем CSV-файл из S3
    response = requests.get(S3_URL)
    df = pd.read_csv(StringIO(response.text), sep=";")  # <-- добавлен sep

    # 2. Приводим имена колонок к нижнему регистру и убираем пробелы
    df.rename(columns=lambda x: x.strip().lower(), inplace=True)
    logging.info(f"Столбцы: {df.columns.tolist()}")

    # 3. Подключение к PostgreSQL
    hook = PostgresHook(postgres_conn_id="psql")
    conn = hook.get_conn()
    cursor = conn.cursor()

    # 4. Сравниваем ID
    cursor.execute("SELECT customer_id FROM clients")
    existing_ids = {row[0] for row in cursor.fetchall()}

    new_rows = df[~df["customerid"].isin(existing_ids)]

    logging.info(f"Найдено новых клиентов: {len(new_rows)}")

    # 5. Вставка новых клиентов
    for _, row in new_rows.iterrows():
        cursor.execute("""
            INSERT INTO clients (
                date, customer_id, surname, credit_score, geography,
                gender, age, tenure, balance, num_of_products,
                has_cr_card, is_active_member, estimated_salary, exited
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['date'], row['customerid'], row['surname'], row['creditscore'],
            row['geography'], row['gender'], row['age'], row['tenure'],
            row['balance'], row['numofproducts'], bool(row['hascrcard']),
            bool(row['isactivemember']), row['estimatedsalary'], bool(row['exited'])
        ))

    conn.commit()
    cursor.close()
    conn.close()

with DAG(
    dag_id="load_credit_clients_from_s3",
    start_date=datetime(2025, 7, 3),
    schedule_interval="@hourly",
    catchup=False,
    default_args=default_args,
    description="Загрузка новых клиентов из S3 в PostgreSQL через Airflow Connection"
) as dag:

    task_load_clients = PythonOperator(
        task_id="load_clients",
        python_callable=update_clients_from_s3
    )
