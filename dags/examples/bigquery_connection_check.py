from airflow import DAG
from airflow.contrib.operators.bigquery_operator import BigQueryGetDatasetOperator


default_args = {
    "depends_on_past": False,
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "email_on_success": False,
    "owner": "airflow",
    "retries": 0,
    "start_date": "2020-01-16 00:00:00",
}

# TODO(developer): update for your specific settings
TASK_PARAMS_DICT = {
    "dataset_id": "dbt_bq_example",
    "project_id": "wam-bam-258119",
    "gcp_conn_id": "my_gcp_connection",
}

with DAG(
    "bigquery_connection_check", default_args=default_args, schedule_interval="@once"
) as dag:
    bigquery_connection_check = BigQueryGetDatasetOperator(
        task_id="bigquery-connection-check",
        dataset_id=TASK_PARAMS_DICT.get("dataset_id"),
        project_id=TASK_PARAMS_DICT.get("project_id"),
        gcp_conn_id=TASK_PARAMS_DICT.get("gcp_conn_id"),
    )

    bigquery_connection_check
