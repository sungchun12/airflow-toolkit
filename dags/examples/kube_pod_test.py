from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.utcnow(),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    # "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "kubernetes_sample",
    default_args=default_args,
    schedule_interval=timedelta(minutes=10),
)


start = DummyOperator(task_id="run_this_first", dag=dag)

passing = KubernetesPodOperator(
    namespace="default",
    image="python:3.6-stretch",
    cmds=["python", "-c"],
    arguments=["print('hello world')"],
    labels={"foo": "bar"},
    name="passing-test",
    task_id="passing-task",
    get_logs=True,
    dag=dag,
)

failing = KubernetesPodOperator(
    namespace="default",
    image="ubuntu:16.04",
    cmds=["python", "-c"],
    arguments=["print('hello world')"],
    labels={"foo": "bar"},
    name="fail",
    task_id="failing-task",
    get_logs=True,
    dag=dag,
)

passing.set_upstream(start)
failing.set_upstream(start)
