# #############################################################################
# Imports
# #############################################################################
import datetime
from airflow import models
from airflow.utils import dates
import google.auth.transport.requests
import json
import os
import time
from airflow.contrib.operators.dataproc_operator import (
    DataprocClusterCreateOperator,
    DataprocClusterDeleteOperator,
)
from airflow.operators.python_operator import PythonOperator

from airflow_utils import get_secret


# TODO: add in config templates
# TODO: add in secrets manager call
# TODO: have someone create a secret: create/delete dataproc cluster and create/delete firewall rules for that dataproc cluster

# #############################################################################
# User configurations
# #############################################################################
PROJECT = "wam-bam-258119"
REGION = "us-central1"
DF_INSTANCE = "dfp"
DF_PIPELINES = ["sample-etl", "sample-etl", "sample-etl", "sample-etl", "sample-etl"]
DF_PIPELINE_POOL = "sql_server_pool"
DATAPROC_CLUSTER_NAME = "etl-cluster"
GCP_CONN_ID_DATAPROC = "my_gcp_connection"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_secret(
    project_name=PROJECT, secret_name="airflow-conn-secret"
)

# #############################################################################
# Constants
# #############################################################################
DATAPROC_API_URL = "https://dataproc.googleapis.com/v1/projects/" + PROJECT
DATAFUSION_API_URL = "https://datafusion.googleapis.com/v1/projects/" + PROJECT
COMPUTE_API_URL = "https://compute.googleapis.com/compute/v1/projects/" + PROJECT


# #############################################################################
# Function to start a pipeline on the predefined Dataproc cluster
# #############################################################################
def start_pipeline_function(pipeline):
    """Start a data fusion pipeline using REST API calls

    Args:
        pipeline(str): name of the pipeline
    Returns:
        response(dict): payload response to indicate done status
    """
    # Default authenication
    # TODO: this will inherit the secrets manager util resetting the env var GOOGLE_APPLICATION_CREDENTIALS
    print("Getting credentials...")
    (credentials, project,) = google.auth.default()
    headers = {"Content-Type": "application/json"}
    request = google.auth.transport.requests.Request()
    credentials.before_request(request=request, method="GET", url="", headers=headers)

    # Get master instance URI
    url = DATAPROC_API_URL + f"/regions/{REGION}/clusters/{DATAPROC_CLUSTER_NAME}"
    response = request(method="GET", url=url, headers=headers, body="")
    print(response.status)
    print(response.data)
    instance_uri = (
        json.loads(response.data)["config"]["gceClusterConfig"]["zoneUri"]
        + "/instances/"
        + json.loads(response.data)["config"]["masterConfig"]["instanceNames"][0]
    )

    # Get IP address of cluster
    url = instance_uri
    print("Getting IP address of Dataproc master")
    response = request(method="GET", url=url, headers=headers, body="")
    ip = json.loads(response.data)["networkInterfaces"][0]["networkIP"]
    print("Got master IP: " + str(ip))

    # Get API endpoint
    print("Getting API endpoint...")
    url = DATAFUSION_API_URL + "/locations/" + REGION + "/instances/" + DF_INSTANCE
    response = request(method="GET", url=url, headers=headers, body="")
    apiEndpointUrl = json.loads(response.data)["apiEndpoint"]
    dfIpAllocation = json.loads(response.data)["networkConfig"]["ipAllocation"]
    print(apiEndpointUrl)
    print(dfIpAllocation)

    # Set IP in Data Fusion config profile
    # TODO: get secrets manager to call private ssh key and dynamically insert into the below
    profile = (
        """{
        "name": "custom-dataproc-cluster",
        "label": "custom-dataproc-cluster",
        "description": "Custom Dataproc cluser for running data fusion pipelines",
        "scope": "SYSTEM",
        "status": "ENABLED",
        "provisioner": {
            "name": "remote-hadoop",
            "properties": [
            {
                "name": "host",
                "value": """
        + '"'
        + str(ip)
        + '"'
        + """,
                "isEditable": true
            },
            {
                "name": "user",
                "value": "hdfs",
                "isEditable": true
            },
            {
                "name": "sshKey",
                "value": "-----BEGIN RSA PRIVATE KEY-----\-----END RSA PRIVATE KEY-----",
                "isEditable": true
            },
            {
                "name": "initializationAction",
                "value": "",
                "isEditable": true
            }
            ]
        }
    }"""
    )

    print("Setting Data Fusion config profile...")
    url = apiEndpointUrl + "/v3/profiles/custom-dataproc-cluster"
    response = request(method="PUT", url=url, headers=headers, body=profile)
    print("status: " + str(response.status))

    # Start the pipeline
    print("Starting the pipeline...")
    url = apiEndpointUrl + "/v3/namespaces/default/start"
    body = (
        '[{"appId": '
        + pipeline
        + ',"programType": "workflow", "programId":"DataPipelineWorkflow", "runtimeargs": { "system.profile.name":"SYSTEM:custom-dataproc-cluster" } }]'
    )
    response = request(method="POST", url=url, headers=headers, body=body)
    print(response.data)
    runId = json.loads(response.data)[0]["runId"]

    # Check for the completion status
    while True:
        url = (
            apiEndpointUrl
            + "/v3/namespaces/default/apps/"
            + pipeline
            + "/workflows/DataPipelineWorkflow/runs/"
            + runId
        )
        response = request(method="GET", url=url, headers=headers, body="")

        time.sleep(10)

        if response.status == 404:
            print("404, waiting...")
        else:
            status = json.loads(response.data)["status"]

            if status == "FAILED" or status == "KILLED" or status == "REJECTED":
                print("BAD: " + status)
                raise Exception(status)
            elif status == "COMPLETED":
                print("GOOD: " + status)
                break
            else:
                print("Still working: " + status)
    return json.loads(response.data)


# #############################################################################
# Function to add a firewall rule allowing Data Fusion to SSH tunnel into Dataproc
# #############################################################################
def add_firewall_function(ds, **kwargs):

    print("Getting credentials...")
    # TODO: this will inherit the secrets manager util resetting the env var GOOGLE_APPLICATION_CREDENTIALS
    credentials, project = google.auth.default()
    headers = {"Content-Type": "application/json"}
    request = google.auth.transport.requests.Request()
    credentials.before_request(request=request, method="GET", url="", headers=headers)

    # Get Data Fusion IP Allocations
    print("Getting Data Fusion IP Allocations...")
    url = DATAFUSION_API_URL + "/locations/" + REGION + "/instances/" + DF_INSTANCE
    response = request(method="GET", url=url, headers=headers, body="")
    dfIpAllocation = json.loads(response.data)["networkConfig"]["ipAllocation"]
    print(dfIpAllocation)
    # targetTags_value = DATAPROC_CLUSTER_NAME

    # TODO: make the targetTags parameterized
    fw_rule = (
        """{
        "name": "etl-cluster-ssh-firewall-rule",
        "description": "Allows Data Fusion to execute pipelines on a single Dataproc cluster",
        "network": "global/networks/default",
        "priority": 1000,
        "sourceRanges": [ """
        + '"'
        + dfIpAllocation
        + '"'
        + """ ],
        "targetTags": [ "etl-cluster" ],
        "allowed": [ { "IPProtocol": "tcp", "ports": [ "22" ] } ]
        }"""
    )

    url = COMPUTE_API_URL + "/global/firewalls"
    credentials.before_request(request=request, method="GET", url=url, headers=headers)

    print("Setting firewall rule")
    response = request(method="POST", url=url, headers=headers, body=fw_rule)
    print(response.status)
    print(response.data)


# #############################################################################
# Function to remove a firewall rule allowing Data Fusion can SSH to Dataproc
# #############################################################################
def remove_firewall_function(ds, **kwargs):
    credentials, project = google.auth.default()
    request = google.auth.transport.requests.Request()
    headers = {"Content-Type": "application/json"}
    url = COMPUTE_API_URL + f"/global/firewalls/{DATAPROC_CLUSTER_NAME}-ssh-firewall-rule"
    credentials.before_request(request=request, method="DELETE", url=url, headers=headers)

    print("Deleting firewall rule")
    response = request(method="DELETE", url=url, headers=headers, body="")
    print(response.status)
    print(response.data)


# #############################################################################
# Function to return the Dataproc configuration for the reusable cluster
# #############################################################################
# def get_dataproc_config():
#     return {
#         "project_id": "data-analytics-webinar",
#         "cluster_name": "{DATAPROC_CLUSTER_NAME}",
#         "config": {
#             "master_config": {
#                 "num_instances": 1,
#                 "machine_type_uri": "n1-standard-4",
#                 "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 1024},
#             },
#             "worker_config": {
#                 "num_instances": 2,
#                 "machine_type_uri": "n1-standard-4",
#                 "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 1024},
#             },
#             "gce_cluster_config": {
#                 "tags": {"{DATAPROC_CLUSTER_NAME}"},
#                 "metadata": {"ssh-keys": "hdfs:ssh-rsa"},
#             },
#         },
#     }


dataproc_config = {
    "cluster_name": DATAPROC_CLUSTER_NAME,
    "num_masters": 1,
    "master_machine_type": "n1-standard-4",
    "master_disk_type": "pd-standard",
    "master_disk_size": 1024,
    "num_workers": 2,
    "worker_machine_type": "n1-standard-4",
    "worker_disk_type": "pd-standard",
    "worker_disk_size": 1024,
    "tags": [DATAPROC_CLUSTER_NAME],
    "metadata": {
        "ssh-keys": "hdfs:ssh-rsa"
    },  # TODO: add public ssh key contents with dynamic secrets manager call
}


# #########################################################
# ##
# ## The DAG
# ##
# #########################################################
default_dag_args = {
    "start_date": dates.days_ago(0),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": datetime.timedelta(minutes=5),
    "project_id": PROJECT,
}

with models.DAG(
    "Weekly-ETL-DAG-5",
    schedule_interval=None,
    start_date=datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.min.time()),
) as dag:

    create_dataproc_cluster = DataprocClusterCreateOperator(
        **dataproc_config,
        task_id="create_dataproc_cluster",
        project_id=PROJECT,
        region=REGION,
        trigger_rule="all_done",
        gcp_conn_id=GCP_CONN_ID_DATAPROC,
    )

    create_firewall_rule = PythonOperator(
        task_id="create_firewall_rule",
        provide_context=True,
        python_callable=add_firewall_function,
        trigger_rule="all_done",
    )

    # start_pipelines = []
    # for x in range(len(DF_PIPELINES)):
    #     start_pipelines.append(
    #         PythonOperator(
    #             task_id=str(x) + "_" + DF_PIPELINES[x],
    #             python_callable=start_pipeline_function,
    #             pool=DF_PIPELINE_POOL,
    #             op_kwargs={"pipeline": DF_PIPELINES[x]},
    #             trigger_rule="all_done",
    #         )
    #     )

    delete_firewall_rule = PythonOperator(
        task_id="delete_firewall_rule",
        provide_context=True,
        python_callable=remove_firewall_function,
        trigger_rule="all_done",
    )

    delete_dataproc_cluster = DataprocClusterDeleteOperator(
        task_id="delete_dataproc_cluster",
        project_id=PROJECT,
        cluster_name=DATAPROC_CLUSTER_NAME,
        region=REGION,
        trigger_rule="all_done",
        gcp_conn_id=GCP_CONN_ID_DATAPROC,
    )

    # Define DAG dependencies.
    # for x in range(len(DF_PIPELINES)):
    #     create_dataproc_cluster >> create_firewall_rule >> start_pipelines[
    #         x
    #     ] >> delete_firewall_rule >> delete_dataproc_cluster

    create_dataproc_cluster >> create_firewall_rule >> delete_firewall_rule >> delete_dataproc_cluster
