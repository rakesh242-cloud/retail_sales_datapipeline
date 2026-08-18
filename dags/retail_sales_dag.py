import sys
from datetime import datetime, timedelta
from airflow.providers.smtp.notifications.smtp import send_smtp_notification

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.append("/opt/airflow/scripts")

from extract import extract as extract_function
from transform import transform as transform_function
from load import load as load_function
from validate import validate_load as validate_function


def transform_task(**context):
    # Récupérer ce que la tâche "extract" a retourné
    extracted_file_path = context["ti"].xcom_pull(
        task_ids="extract"
    )

    print("Fichier reçu depuis extract :", extracted_file_path)

    # Lancer notre vraie transformation
    return transform_function(extracted_file_path)


def load_task(**context):
    transform_result = context["ti"].xcom_pull(
        task_ids="transform"
    )

    clean_file = transform_result["clean_file"]
    rejected_file = transform_result["rejected_file"]

    return load_function(
        clean_file,
        rejected_file
    )


def validate_task(**context):
    import pandas as pd

    # Récupérer les fichiers produits par transform
    transform_result = context["ti"].xcom_pull(
        task_ids="transform"
    )

    clean_file = transform_result["clean_file"]
    rejected_file = transform_result["rejected_file"]

    # Lire les fichiers pour connaître les volumes attendus
    clean_df = pd.read_pickle(clean_file)
    rejected_df = pd.read_pickle(rejected_file)

    expected_clean = len(clean_df)
    expected_rejected = len(rejected_df)

    print("Clean attendu :", expected_clean)
    print("Rejected attendu :", expected_rejected)

    # Comparer avec ce qui existe réellement dans PostgreSQL
    return validate_function(
        expected_clean,
        expected_rejected
    )


failure_email = send_smtp_notification(
    smtp_conn_id="smtp_default",
    from_email="joubair.ayoub96@gmail.com",
    to="joubair.ayoub96@gmail.com",
    subject="Airflow - Task failed",
    html_content="Une tâche du pipeline retail_sales_pipeline a échoué."
)

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": failure_email,
}


with DAG(
    dag_id="retail_sales_pipeline",
    start_date=datetime(2026, 8, 13),
    schedule="0 2 * * *",
    catchup=False,
    default_args=default_args,
) as dag:

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_function
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task
    )

    load = PythonOperator(
        task_id="load",
        python_callable=load_task
    )

    validate = PythonOperator(
        task_id="validate_load",
        python_callable=validate_task
    )

    extract >> transform >> load >> validate