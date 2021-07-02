from airflow import DAG
from datetime import datetime
from airflow.operators.python_operator import PythonOperator
from dbt_cloud_utils import dbt_cloud_job_runner


dag_file_name = __file__
# example dbt Cloud job config
dbt_cloud_job_runner_config = dbt_cloud_job_runner(
    account_id=4238, project_id=12220, job_id=12389, cause=dag_file_name
)


default_args = {
    "owner": "airflow",
    "email": ["airflow@example.com"],
    "depends_on_past": False,
    "start_date": datetime(2001, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "priority_weight": 1000,
}


with DAG(
    "dbt_cloud_example", default_args=default_args, schedule_interval="@once"
) as dag:

    # Single task to execute dbt Cloud job
    t1 = PythonOperator(
        task_id="run-dbt-cloud-job",
        python_callable=dbt_cloud_job_runner_config.run_job,
        provide_context=True,
    )

    t1
