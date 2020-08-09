import pytest
from airflow.models import DagBag, TaskInstance
from datetime import datetime
import time
from google.cloud import secretmanager

# import created modules
import dags.dbt_kube_dag as pilot_pipeline
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
import json
from airflow import DAG, settings
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
import os
import subprocess


# https://blog.usejournal.com/testing-in-airflow-part-1-dag-validation-tests-dag-definition-tests-and-unit-tests-2aa94970570c

"""Tests the airflow commands and verifies 
successful connections to the proper environments
"""

# Global Vars
PIPELINE = "dbt_kube_dag"  # DAG to be tested
PROJECT_NAME = os.environ["DBT_DATABASE"].lower()  # GCP project where BQ resides
ENVIRONMENT = os.environ["ENV"].lower()

DEFAULT_ARGS = Variable.get(f"{PIPELINE}_default_args", deserialize_json=True)
RUNTIME_PARAMETERS = Variable.get(
    f"{PIPELINE}_runtime_parameters", deserialize_json=True
)
DBT_COMMANDS = Variable.get(f"{PIPELINE}_dbt_commands", deserialize_json=True)


@pytest.fixture
def get_test_configs():
    """Retrieve test configurations, primarily for cloud composer end to end testing
    This can be extended to include more specific test configurations
    """
    with open(
        f"/pytest/dag_environment_configs/{ENVIRONMENT}/{PIPELINE}_pytest_{ENVIRONMENT}.json",
        "r",
    ) as openfile:
        # read in the file
        json_object = json.load(openfile)
        test_configs = json_object.get("test_configs")

    return test_configs


@pytest.fixture
def setup_method():
    """ setup any state specific to the execution of the given class (which
    usually contains tests).
    """
    dag_folder = "/pytest/"
    setup_dagbag = DagBag(dag_folder=dag_folder)
    return setup_dagbag


@pytest.fixture
def reset_pytest_airflow_vars():
    """reset arguments back to default"""
    with open(
        f"/pytest/dag_environment_configs/{ENVIRONMENT}/{PIPELINE}_pytest_{ENVIRONMENT}.json",
        "r",
    ) as openfile:
        # read in the file
        json_object = json.load(openfile)

        # set the airflow variables
        Variable.set(
            f"{PIPELINE}_runtime_parameters",
            json.dumps(json_object[f"{PIPELINE}_runtime_parameters"]),
        )
        Variable.set(
            f"{PIPELINE}_default_args",
            json.dumps(json_object[f"{PIPELINE}_default_args"]),
        )
        Variable.set(
            f"{PIPELINE}_dbt_commands",
            json.dumps(json_object[f"{PIPELINE}_dbt_commands"]),
        )
    print("Reset Airflow Variables to pytest defaults")


def test_import_dags(setup_method, reset_pytest_airflow_vars):
    """Test the dags imported have no syntax errors
    """
    reset_pytest_airflow_vars
    dag_errors_message = len(setup_method.import_errors)
    assert dag_errors_message == 0


def test_contains_tasks(setup_method, reset_pytest_airflow_vars):
    """Test that the DAG only contains the tasks expected"""
    reset_pytest_airflow_vars
    dag_id = PIPELINE
    dag = setup_method.get_dag(dag_id)
    task_ids = list(map(lambda task: task.task_id, dag.tasks))
    assert any("dbt" in s for s in task_ids) == True
    assert task_ids == ["dummy_task_1", "dbt-run", "dbt-test"]


def test_schedule(setup_method, reset_pytest_airflow_vars):
    """Test that the DAG only contains the schedule expected"""
    reset_pytest_airflow_vars
    dag_id = PIPELINE
    dag = setup_method.get_dag(dag_id)
    assert dag._schedule_interval == None


def test_task_count_pilot_pipeline(setup_method, reset_pytest_airflow_vars):
    """Check task count of pilot_pipeline_dynamic_template dag"""
    reset_pytest_airflow_vars
    dag_id = PIPELINE
    dag = setup_method.get_dag(dag_id)
    dag_task_count = len(dag.tasks)

    # dbt_debug
    static_expected_task_count = 1
    # other dbt commands
    dynamic_expected_task_count = len(
        Variable.get(f"{PIPELINE}_dbt_commands", deserialize_json=True)
    )
    total_expected_task_count = static_expected_task_count + dynamic_expected_task_count

    assert dag_task_count == total_expected_task_count


dbt_task_list = [
    "dbt-debug",
    "dbt-run" "dbt-test",
]
# TODO(developer): airflow tests will NOT overwrite existing tables. These simply test if all dbt tasks run through successfully.
@pytest.mark.parametrize("dbt_task", dbt_task_list)
def test_dbt_tasks(dbt_task, reset_pytest_airflow_vars):
    "Tests that dbt tasks in scope operate as expected"
    reset_pytest_airflow_vars
    task = getattr(pilot_pipeline, dbt_task)  # dynamically call attribute function call
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())


# test fixtures utilized in tests below
dbt_command_empty = {}

dbt_command_duplicate = {
    "dbt_source_freshness": "dbt source snapshot-freshness --select status.table_name",
    "dbt_source_freshness": "dbt source snapshot-freshness --select status.table_name",
}

dbt_command_full = {
    "dbt_test_status": "dbt test --models source:status.table_name",
    "dbt_source_freshness": "dbt source snapshot-freshness --select status.table_name",
    "dbt_run": "dbt run --models model_source.table_name",
    "dbt_test_transformed": "dbt test --models model_source.table_name",
}


@pytest.fixture(
    params=[
        pytest.param(dbt_command_empty, id="dbt_command_empty"),
        pytest.param(dbt_command_duplicate, id="dbt_command_duplicate"),
        pytest.param(dbt_command_full, id="dbt_command_full"),
    ]
)
def dbt_task_generator(request, reset_pytest_airflow_vars):
    """Setup task generator for dbt"""
    reset_pytest_airflow_vars

    # create the utility
    dynamic_task_generator = pilot_pipeline.dynamic_task_generator_utility()

    # set dbt_commands
    dynamic_task_generator.dbt_commands = request.param

    return dynamic_task_generator


def test_dbt_dynamic_tasks(dbt_task_generator, reset_pytest_airflow_vars):
    """Tests that dbt_dynamic_tasks gets generated as expected"""

    default_args = dbt_task_generator.default_args
    dbt_commands = dbt_task_generator.dbt_commands

    # create a completely separate dag during test runtime
    with DAG(
        "test_dbt_dynamnic_tasks", default_args=default_args, schedule_interval=None
    ):
        dbt_dynamic_tasks = dbt_task_generator.dbt_dynamic_tasks()

    # compare created and input tasks
    created_tasks = [(task.task_id, task.command) for task in dbt_dynamic_tasks]
    input_tasks = [(task_id, command) for task_id, command in dbt_commands.items()]

    assert created_tasks == input_tasks

    reset_pytest_airflow_vars


def test_sequential_append_dbt(dbt_task_generator, reset_pytest_airflow_vars):
    """Tests sequential appending for dbt_commands"""

    # (1) A dag generated using sequential_append
    # ---------------------------------
    dag = DAG(
        "test_sequential_append_dbt",
        default_args=dbt_task_generator.default_args,
        schedule_interval=None,
    )
    with dag:
        # create a dummy task to append dbt tasks
        dummy_task = DummyOperator(task_id="dbt_dummy_task")

        # generate dbt tasks using dbt_commands in airflow variable
        dbt_dynamic_tasks = dbt_task_generator.dbt_dynamic_tasks()

        # append dbt tasks to the dummy task
        dbt_task_generator.sequential_append(
            to_task=dummy_task, from_task_list=dbt_dynamic_tasks
        )

    # (2) A dag generated without using sequential_append
    # ---------------------------------
    dag_expected = DAG(
        "test_sequential_append_dbt_expected",
        default_args=dbt_task_generator.default_args,
        schedule_interval=None,
    )
    with dag_expected:
        # create a dummy task to append dbt tasks
        dummy_task = DummyOperator(task_id="dbt_dummy_task")

        # generate dbt tasks using dbt_commands in airflow variable
        dbt_dynamic_tasks = dbt_task_generator.dbt_dynamic_tasks()

        if dbt_dynamic_tasks:
            # set first task from dbt_dynamic_tasks as dummy_task's downstream
            dummy_task >> dbt_dynamic_tasks[0]

            # chain dbt tasks
            for up_task, down_task in zip(
                dbt_dynamic_tasks[:-1], dbt_dynamic_tasks[1:]
            ):
                up_task >> down_task

    # validate dependencies from tasks in dag (1) and dag (2)
    for dag_task, expected_task in zip(dag.tasks, dag_expected.tasks):
        assert dag_task.task_id == expected_task.task_id
        assert dag_task.downstream_list == expected_task.downstream_list

    reset_pytest_airflow_vars


@pytest.fixture
def get_secret(project_name, secret_name):
    secrets = secretmanager.SecretManagerServiceClient()
    secret_value = (
        secrets.access_secret_version(
            "projects/" + project_name + "/secrets/" + secret_name + "/versions/latest"
        )
        .payload.data.decode("utf-8")
        .replace("\n", "")
    )
    return secret_value


def test_end_to_end_pipeline(reset_pytest_airflow_vars, get_test_configs, get_secret):
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

    # upload reset_dag_configs_{ENVIRONMENT_CONFIG}.json into cloud storage bucket for cloud composer
    file_location_config = f"/pytest/dag_environment_configs/{ENVIRONMENT}/{PIPELINE}_pytest_{ENVIRONMENT}.json"
    blob_config = bucket.blob(
        f"data/dag_environment_configs/{ENVIRONMENT}/"
        + "{PIPELINE}_pytest_{ENVIRONMENT}.json"
    )
    blob_config.upload_from_filename(file_location_config)

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
