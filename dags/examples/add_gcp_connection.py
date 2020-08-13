import json

from airflow import DAG, settings
from airflow.models import Connection
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

default_args = {
    "owner": "airflow",
    "email": ["airflow@example.com"],
    "depends_on_past": False,
    "start_date": datetime(2001, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 5,
    "priority_weight": 1000,
}

# TODO: reference private repo with a draft of using secrets manager vs. a hard-coded file
default_params = {
    "gcp_project": "wam-bam-258119",
    "key_file_path": "/account.json",
    "gcp_conn_id": "my_gcp_connection",
    "gcr_conn_id": "gcr_docker_connection",
}


def add_gcp_connection(ds, **kwargs):
    """"Add a airflow connection for GCP"""
    new_conn = Connection(conn_id=default_params["gcp_conn_id"], conn_type="google_cloud_platform",)
    scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    conn_extra = {
        "extra__google_cloud_platform__scope": ",".join(scopes),
        "extra__google_cloud_platform__project": default_params["gcp_project"],
        "extra__google_cloud_platform__key_path": default_params["key_file_path"],
    }
    conn_extra_json = json.dumps(conn_extra)
    new_conn.set_extra(conn_extra_json)

    session = settings.Session()
    if not (session.query(Connection).filter(Connection.conn_id == new_conn.conn_id).first()):
        session.add(new_conn)
        session.commit()
        msg = "\n\tA connection with `conn_id`={conn_id} is newly created\n"
        msg = msg.format(conn_id=new_conn.conn_id)
        print(msg)
    else:
        msg = "\n\tA connection with `conn_id`={conn_id} already exists\n"
        msg = msg.format(conn_id=new_conn.conn_id)
        print(msg)


# https://github.com/apache/airflow/blob/master/airflow/models/connection.py
def add_docker_connection(ds, **kwargs):
    """"Add a airflow connection for google container registry"""
    new_conn = Connection(
        conn_id=default_params["gcr_conn_id"],
        conn_type="docker",
        host="gcr.io/" + default_params["gcp_project"],
        login="_json_key",
    )

    # save contents of service account key into encrypted password field
    with open(default_params["key_file_path"], "r") as file:
        data = file.read().replace("\\n", "\n")  # replace new lines
        new_conn.set_password(data)

    session = settings.Session()
    if not (session.query(Connection).filter(Connection.conn_id == new_conn.conn_id).first()):
        session.add(new_conn)
        session.commit()
        msg = "\n\tA connection with `conn_id`={conn_id} is newly created\n"
        msg = msg.format(conn_id=new_conn.conn_id)
        print(msg)
    else:
        msg = "\n\tA connection with `conn_id`={conn_id} already exists\n"
        msg = msg.format(conn_id=new_conn.conn_id)
        print(msg)


with DAG("add_gcp_connection", default_args=default_args, schedule_interval="@once") as dag:

    # Task to add a google cloud connection
    t1 = PythonOperator(
        task_id="add_gcp_connection_python",
        python_callable=add_gcp_connection,
        provide_context=True,
    )

    # Task to add a google container registry connection
    t2 = PythonOperator(
        task_id="add_docker_connection_python",
        python_callable=add_docker_connection,
        provide_context=True,
    )

    t1 >> t2
