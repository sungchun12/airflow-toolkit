import pytest
from airflow.models import DagBag, TaskInstance
from datetime import datetime
import time

# import created modules
import dags.examples.add_gcp_connections as test_dag
from airflow.operators.dummy_operator import DummyOperator
import json
from airflow import DAG, settings
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
import os
import subprocess


# Reference Blog: https://blog.usejournal.com/testing-in-airflow-part-1-dag-validation-tests-dag-definition-tests-and-unit-tests-2aa94970570c

"""Tests the airflow commands and verifies 
successful connections to the proper environments
"""


os.environ["DBT_DATABASE"] = "wam-bam-258119"
os.environ["ENV"] = "dev"

# Global Vars
PIPELINE = "add_gcp_connections"  # DAG to be tested
PROJECT_NAME = os.environ["DBT_DATABASE"].lower()  # GCP project where BQ resides
ENVIRONMENT = os.environ["ENV"].lower()  # dev, qa, prod


@pytest.fixture
def setup_method():
    """ setup any state specific to the execution of the given class (which
    usually contains tests).
    """
    dag_folder = (
        "/opt/airflow/dags/"  # TODO: make this dynamic for the cloud composer path
    )
    setup_dagbag = DagBag(dag_folder=dag_folder)
    return setup_dagbag


def test_import_dags(setup_method):
    """Test the dags imported have no syntax errors
    """
    dag_errors_message = len(setup_method.import_errors)
    assert dag_errors_message == 0


def test_contains_tasks(setup_method):
    """Test that the DAG only contains the tasks expected"""
    dag_id = PIPELINE
    dag = setup_method.get_dag(dag_id)
    task_ids = list(map(lambda task: task.task_id, dag.tasks))
    assert task_ids == ["add-gcp-connection-python", "add-docker-connection-python"]


def test_task_dependencies(setup_method):
    """Check the task dependencies of the dag dag"""
    # gcp connection task upstream and downstream task dependencies
    gcp_conn_task = getattr(test_dag, "t1")
    upstream_task_ids = list(
        map(lambda task: task.task_id, gcp_conn_task.upstream_list)
    )
    assert upstream_task_ids == []
    downstream_task_ids = list(
        map(lambda task: task.task_id, gcp_conn_task.downstream_list)
    )
    assert downstream_task_ids == []

    # google container registry connection task upstream and downstream task dependencies
    gcr_conn_task = getattr(test_dag, "t2")
    upstream_task_ids = list(
        map(lambda task: task.task_id, gcr_conn_task.upstream_list)
    )
    assert upstream_task_ids == []
    downstream_task_ids = list(
        map(lambda task: task.task_id, gcr_conn_task.downstream_list)
    )
    assert downstream_task_ids == []


def test_schedule(setup_method):
    """Test that the DAG only contains the schedule expected"""
    dag_id = PIPELINE
    dag = setup_method.get_dag(dag_id)
    assert dag.schedule_interval == "@once"


def test_task_count_test_dag(setup_method):
    """Check task count of test_dag_dynamic_template dag"""
    dag_id = PIPELINE
    dag = setup_method.get_dag(dag_id)
    dag_task_count = len(dag.tasks)

    total_expected_task_count = 2

    assert dag_task_count == total_expected_task_count


task_list = [
    "t1",
    "t2",
]


@pytest.mark.parametrize("task_to_run", task_list)
def test_tasks(task_to_run, capfd):
    "Tests that dbt tasks in scope operate as expected"
    expected_result_dict = {
        "t1": [
            "\n\tA connection with `conn_id`=my_gcp_connection is newly created\n\n",
            "\n\tA connection with `conn_id`=my_gcp_connection already exists\n\n",
        ],
        "t2": [
            "\n\tA connection with `conn_id`=gcr_docker_connection is newly created\n\n",
            "\n\tA connection with `conn_id`=gcr_docker_connection already exists\n\n",
        ],
    }
    try:
        task = getattr(
            test_dag, task_to_run
        )  # dynamically call attribute function call
        ti = TaskInstance(task=task, execution_date=datetime.now())
        result = task.execute(ti.get_template_context())
        out, err = capfd.readouterr()
        assert (
            out == expected_result_dict.get(task_to_run)[0]
        )  # dynamic assertion key value pair
    except AssertionError:
        assert out == expected_result_dict.get(task_to_run)[1]


# TODO: to be drafted later
@pytest.mark.skip(reason="waiting until cloud composer is deployed first")
def test_end_to_end_pipeline(get_secret):
    """
    Runs the DAG end to end in cloud composer
    The end to end test is distinct from the other tests as this ensures the whole DAG runs in cloud composer successfully
    The other tests focus on component functionality within a local airflow environment as it is not feasible to do so within cloud composer at this time
    """
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # define the project and bucket to upload dag and config files for cloud composer testing
    test_configs = get_test_configs
    project_id = PROJECT_NAME
    bucked_id = test_configs.get("bucked_id")
    cloud_composer_id = test_configs.get("cloud_composer_id")

    # ensures correct permissions are used
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_secret(
        project_name=PROJECT_NAME, secret_name="SERVICE_ACCOUNT"
    )

    # upload dag to cloud storage bucket for cloud composer
    client = storage.Client(project=project_id)
    bucket = client.get_bucket(bucked_id)
    file_location_dag = f"/pytest/dags/{PIPELINE}.py"
    blob_dag = bucket.blob(f"dags/" + "{PIPELINE}.py")
    blob_dag.upload_from_filename(file_location_dag)

    # upload pipeline configs in scope to cloud storage bucket for cloud composer
    for config_file in reset_dag_configs_generator.reset_configs_in_scope_list:
        file_location = (
            reset_dag_configs_generator.reset_configs_directory_in_scope + config_file
        )
        blob = bucket.blob(f"data/dag_environment_configs/{ENVIRONMENT}/" + config_file)
        blob.upload_from_filename(file_location)

    # gcloud command to import variables into cloud composer
    command = f"gcloud composer environments run {cloud_composer_id} variables -- --import /home/airflow/gcsfuse/dag_environment_configs/{ENVIRONMENT}/{PIPELINE}_pytest_{ENVIRONMENT}.json"
    process = subprocess.run(command.split())
    assert process.returncode == 0  # should be 0

    # wait 40 seconds for cloud composer to update the DAG within the database
    time.sleep(40)

    # run the the full pipeline without errors
    # TODO: run a backfill command
    command = f"gcloud composer environments run {cloud_composer_id} backfill -- {PIPELINE} -s 2020-01-01 -e 2020-01-02 --reset_dagruns"
    process = subprocess.run(command.split())
    assert process.returncode == 0  # should be 0
