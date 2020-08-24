import json
import os
from airflow import DAG, settings
from airflow.models import Connection
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from airflow_utils import DEPLOYMENT_SETUP, get_secret, set_google_app_credentials

# TODO(developer)
# # create a secrets manager secret from the local service accountkey
# gcloud secrets create airflow-conn-secret \
#     --replication-policy="automatic" \
#     --data-file=service_account.json

# # List the secret
# gcloud secrets list

# # verify secret contents ad hoc
# gcloud secrets versions access latest --secret="airflow-conn-secret"

# TODO(developer): for cloud composer, IAM policies will be assumed while running this DAG
# this must be set for the local kubernetes setup to work
# this can be removed for the cloud composer version of the DAG
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/account.json"
dag_name = "add_gcp_connections"
set_google_app_credentials(DEPLOYMENT_SETUP,dag_name)

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

# TODO(developer): update for your specific naming conventions
CONN_PARAMS_DICT = {
    "gcp_project": "wam-bam-258119",
    "gcp_conn_id": "my_gcp_connection",
    "gcr_conn_id": "gcr_docker_connection",
    "secret_name": "airflow-conn-secret",
}


def add_gcp_connection(ds, **kwargs):
    """"Add a airflow connection for GCP"""
    new_conn = Connection(
        conn_id=CONN_PARAMS_DICT["gcp_conn_id"], conn_type="google_cloud_platform",
    )
    scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    conn_extra = {
        "extra__google_cloud_platform__scope": ",".join(scopes),
        "extra__google_cloud_platform__project": CONN_PARAMS_DICT.get("gcp_project"),
        "extra__google_cloud_platform__keyfile_dict": get_secret(
            project_name=CONN_PARAMS_DICT.get("gcp_project"),
            secret_name=CONN_PARAMS_DICT.get("secret_name"),
        ),
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
        conn_id=CONN_PARAMS_DICT.get("gcr_conn_id"),
        conn_type="docker",
        host="gcr.io/" + CONN_PARAMS_DICT.get("gcp_project"),
        login="_json_key",
    )

    # save contents of service account key into encrypted password field
    json_key = get_secret(
        project_name=CONN_PARAMS_DICT.get("gcp_project"),
        secret_name=CONN_PARAMS_DICT.get("secret_name"),
    )
    data = str(json.loads(json_key))
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


with DAG(dag_name, default_args=default_args, schedule_interval="@once") as dag:

    # Task to add a google cloud connection
    t1 = PythonOperator(
        task_id="add-gcp-connection-python",
        python_callable=add_gcp_connection,
        provide_context=True,
    )

    # Task to add a google container registry connection
    t2 = PythonOperator(
        task_id="add-docker-connection-python",
        python_callable=add_docker_connection,
        provide_context=True,
    )

    [t1, t2]
