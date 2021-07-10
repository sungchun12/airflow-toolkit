from airflow import DAG
from datetime import datetime
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator

from airflow_utils import pod_env_vars, DBT_IMAGE


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
    schedule_interval="@once",
)


start = DummyOperator(task_id="run_this_first", dag=dag)

# intentionally pointing to "default" kubernetes namespace to illustrate that pods can run in different environments
# "default" should work for cloud composer as well
passing_python = KubernetesPodOperator(
    namespace="default",
    image="python:3.7-slim",
    cmds=["python", "-c"],
    arguments=["print('hello world')"],
    labels={"foo": "bar"},
    name="passing-python",
    task_id="passing-python-task",
    get_logs=True,
    dag=dag,
)

passing_bash = KubernetesPodOperator(
    namespace="default",
    image="ubuntu:16.04",
    cmds=["/bin/bash", "-cx"],
    arguments=["mkdir -p /airflow/xcom/;echo '[1,2,3,4]' > /airflow/xcom/return.json"],
    labels={"foo": "bar"},
    name="passing-bash-task",
    task_id="passing-bash-task",
    get_logs=True,
    do_xcom_push=True,
    dag=dag,
)

private_gcr_passing = KubernetesPodOperator(
    namespace="default",
    image=DBT_IMAGE,
    cmds=["python", "-c"],
    arguments=["print('hello world')"],
    labels={"foo": "bar"},
    name="private-gcr-passing",
    task_id="private-gcr-passing-task",
    get_logs=True,
    # Storing sensitive credentials in env_vars will be exposed in plain text
    env_vars=pod_env_vars,
    dag=dag,
)

bash_task_xcom_result = BashOperator(
    bash_command="echo \"{{ task_instance.xcom_pull('passing-bash-task')[0] }}\"",
    task_id="bash_task_xcom_result",
    dag=dag,
)

# xcom pull follows a different syntax compared to the BashOperator
pod_task_xcom_result = KubernetesPodOperator(
    namespace="default",
    image="ubuntu:16.04",
    cmds=["/bin/bash", "-c"],
    arguments=["echo \"{{ task_instance.xcom_pull(task_ids='passing-bash-task', key='return_value')[0] }}\""],
    labels={"foo": "bar"},
    name="pod_task_xcom_result",
    task_id="pod_task_xcom_result",
    get_logs=True,
    dag=dag,
)


start >> [passing_python, passing_bash, private_gcr_passing]

passing_bash >> [bash_task_xcom_result, pod_task_xcom_result]
