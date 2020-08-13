from airflow import DAG
from datetime import datetime
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from kube_secrets import DBT_SERVICE_ACCOUNT, GIT_SECRET_ID_RSA_PRIVATE
from airflow_utils import kube_pod_defaults, pod_env_vars, dbt_setup_cmds, DBT_IMAGE

pod_env_vars = {**pod_env_vars, **{}}

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

dbt_debug_cmd = f"""
    {dbt_setup_cmds} &&
    dbt debug --target service_account_runs
"""

dbt_run_cmd = f"""
    {dbt_setup_cmds} &&
    dbt run --target service_account_runs
"""

dbt_test_cmd = f"""
    {dbt_setup_cmds} &&
    dbt test --target service_account_runs
"""

with DAG("dbt_example", default_args=default_args, schedule_interval="@once") as dag:

    dbt_debug = KubernetesPodOperator(
        **kube_pod_defaults,
        image=DBT_IMAGE,
        task_id="dbt-debug",
        name="dbt-debug",
        arguments=[dbt_debug_cmd],
        secrets=[DBT_SERVICE_ACCOUNT, GIT_SECRET_ID_RSA_PRIVATE],
        # Storing sensitive credentials in env_vars will be exposed in plain text
        env_vars=pod_env_vars,
    )

    dbt_run = KubernetesPodOperator(
        **kube_pod_defaults,
        image=DBT_IMAGE,
        task_id="dbt-run",
        name="dbt-run",
        arguments=[dbt_run_cmd],
        secrets=[DBT_SERVICE_ACCOUNT, GIT_SECRET_ID_RSA_PRIVATE],
        # Storing sensitive credentials in env_vars will be exposed in plain text
        env_vars=pod_env_vars,
    )

    dbt_test = KubernetesPodOperator(
        **kube_pod_defaults,
        image=DBT_IMAGE,
        task_id="dbt-test",
        name="dbt-test",
        arguments=[dbt_test_cmd],
        secrets=[DBT_SERVICE_ACCOUNT, GIT_SECRET_ID_RSA_PRIVATE],
        # Storing sensitive credentials in env_vars will be exposed in plain text
        env_vars=pod_env_vars,
    )

    dbt_debug >> dbt_run >> dbt_test
