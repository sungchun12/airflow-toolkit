"""Full test suite for the DAG: reset_dag_configs.py
Component-level testing is passed within a local airflow docker environment
End to end testing is passed within cloud composer
"""

import pytest
import json
from airflow import DAG
from airflow.models import DagBag, TaskInstance, Variable
from datetime import datetime
import subprocess
import time
import os
from google.cloud import storage

# import DAG
import dags.reset_dag_configs as reset_dag_configs

# determines whether these tests run under configurations: dev, qa, prod
# this environment variable is built into the pytest container during runtime
ENVIRONMENT_CONFIG = os.environ["ENV"].lower()


@pytest.fixture
def get_test_configs():
    """Retrieve test configurations, primarily for cloud composer end to end testing
    This can be extended to include more specific test configurations
    """
    with open(
        f"/pytest/dag_environment_configs/{ENVIRONMENT_CONFIG}/reset_dag_configs_{ENVIRONMENT_CONFIG}_pytest.json",
        "r",
    ) as openfile:
        # read in the file
        json_object = json.load(openfile)
        test_configs = json_object.get("test_configs")

    return test_configs


@pytest.fixture
def setup_method():
    """Setup Dag location
    """
    dag_folder = "/pytest/dags/"
    setup_dagbag = DagBag(dag_folder=dag_folder)
    return setup_dagbag


@pytest.fixture
def reset_pytest_airflow_vars():
    """Reset arguments back to default and define the class utility"""
    with open(
        f"/pytest/dag_environment_configs/{ENVIRONMENT_CONFIG}/reset_dag_configs_{ENVIRONMENT_CONFIG}_pytest.json",
        "r",
    ) as openfile:
        # read in the file
        json_object = json.load(openfile)

        # set the airflow variables
        Variable.set(
            "reset_configs_default_args",
            json.dumps(json_object["reset_configs_default_args"]),
        )
        Variable.set(
            "reset_configs_in_scope_list",
            json.dumps(json_object["reset_configs_in_scope_list"]),
        )
        Variable.set(
            "reset_configs_directory_in_scope",
            json.dumps(json_object["reset_configs_directory_in_scope"]),
        )
    reset_dag_configs_generator = reset_dag_configs.reset_dag_configs_utility()
    print("Reset Airflow Variables to pytest defaults")
    return reset_dag_configs_generator


def test_import_dags(setup_method, reset_pytest_airflow_vars):
    """Test the DAGs imported have no syntax errors
    """
    reset_pytest_airflow_vars
    dag_errors_message = len(setup_method.import_errors)
    assert dag_errors_message == 0


def test_task_count_reset_dag_configs(setup_method, reset_pytest_airflow_vars):
    """Check task count of reset_dag_configs DAG"""
    reset_pytest_airflow_vars
    dag_id = "reset_dag_configs"
    dag = setup_method.get_dag(dag_id)
    dag_task_count = len(dag.tasks)
    expected_result = 1
    assert dag_task_count == expected_result


def test_contains_tasks(setup_method, reset_pytest_airflow_vars):
    """Test that the DAG only contains the tasks expected"""
    reset_pytest_airflow_vars
    dag_id = "reset_dag_configs"
    dag = setup_method.get_dag(dag_id)
    task_ids = list(map(lambda task: task.task_id, dag.tasks))
    assert task_ids == ["reset_dag_configs_task"]


def test_schedule(setup_method, reset_pytest_airflow_vars):
    """Test that the DAG only contains the schedule expected"""
    reset_pytest_airflow_vars
    dag_id = "reset_dag_configs"
    dag = setup_method.get_dag(dag_id)
    assert dag._schedule_interval == "0 11 * * *"


def test_reset_dag_configs_utility_init(reset_pytest_airflow_vars):
    """Test that class method: `reset_configs_default_args` functions as expected"""
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # assert the utility init variables match variables uploaded to airflow
    assert reset_dag_configs_generator.reset_configs_default_args == Variable.get(
        "reset_configs_default_args", deserialize_json=True
    )
    assert reset_dag_configs_generator.reset_configs_in_scope_list == Variable.get(
        "reset_configs_in_scope_list", deserialize_json=True
    )
    assert (
        reset_dag_configs_generator.reset_configs_directory_in_scope
        == Variable.get("reset_configs_directory_in_scope", deserialize_json=True)[0]
    )  # string object


def test_validate_no_duplicate_config_vars_success(reset_pytest_airflow_vars, capfd):
    """Test that class method: `validate_no_duplicate_config_vars` functions as expected when successful"""
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # run the function
    reset_dag_configs_generator.validate_no_duplicate_config_vars()

    # assert the print statement matches
    expected_result = f"There are no duplicate variables within {reset_dag_configs_generator.reset_configs_in_scope_list} based on files in this location: {reset_dag_configs_generator.reset_configs_directory_in_scope}"
    out, err = capfd.readouterr()
    assert expected_result in out.strip("\n")


def test_validate_no_duplicate_config_vars_fail(reset_pytest_airflow_vars, capfd):
    """Test that class method: `validate_no_duplicate_config_vars` functions as expected when failed"""
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # add a duplicate variable name
    duplicate_vars_1 = {"default_args": 1}
    duplicate_vars_2 = {"default_args": 2}

    # write the duplicate vars to a temporary json config file
    with open(
        f"/pytest/dag_environment_configs/{ENVIRONMENT_CONFIG}/duplicate_vars_1.json",
        "w",
    ) as file:
        file.write(json.dumps(duplicate_vars_1))
    with open(
        f"/pytest/dag_environment_configs/{ENVIRONMENT_CONFIG}/duplicate_vars_2.json",
        "w",
    ) as file:
        file.write(json.dumps(duplicate_vars_2))

    # append it to the configs in scope list
    reset_dag_configs_generator.reset_configs_in_scope_list.append(
        "duplicate_vars_1.json"
    )
    reset_dag_configs_generator.reset_configs_in_scope_list.append(
        "duplicate_vars_2.json"
    )
    with pytest.raises(SystemExit):
        # run the function
        reset_dag_configs_generator.validate_no_duplicate_config_vars()

        # expected result
        expected_result = ["default_args"]

        # assert the print statement matches
        out, err = capfd.readouterr()

        expected_result_print = f"These are the duplicate variables {expected_result} within {reset_dag_configs_generator.reset_configs_in_scope_list} based on files in this location: {reset_dag_configs_generator.reset_configs_directory_in_scope}"

        expected_sys_exit_print = "Stopping the DAG now!"

        assert expected_result_print in out.strip("\n")
        assert expected_sys_exit_print in out.strip("\n")


def test_set_dag_configs(reset_pytest_airflow_vars, capfd):
    """Test that class method: `set_dag_configs` functions as expected"""
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # run the function
    reset_dag_configs_generator.set_dag_configs()

    # assert the terminal output
    expected_print = "Uploaded Airflow Variables"
    out, err = capfd.readouterr()
    assert expected_print == out.strip("\n")

    # Variable.get to retrieve all the variables similar to get_dag_configs logic
    # use a specific variable to test
    # similar logic to the get_dag_configs() method but isolated to a single config file
    config_file = "finance_daily_dev.json"
    file_location = (
        reset_dag_configs_generator.reset_configs_directory_in_scope + config_file
    )
    with open(file_location, "r") as openfile:
        json_object = json.load(openfile)  # read in the file

        # get the airflow variables in dict comprehension
        airflow_variables = {
            k: Variable.get(k, deserialize_json=True) for k, v in json_object.items()
        }

        # match contents of config file across each airflow variable
        for key in json_object.keys():
            assert json_object[key] == airflow_variables[key]


def test_get_dag_configs(reset_pytest_airflow_vars, capfd):
    """Test that class method: `get_dag_configs` functions as expected"""
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # run the function
    # this is a self-validating method so this test needs to validate if the print message matches as expected
    reset_dag_configs_generator.get_dag_configs()

    # assert the terminal output
    expected_print = "Validated Airflow Variables match config file contents"
    out, err = capfd.readouterr()
    assert expected_print == out.strip("\n")


def test_reset_dag_configs_task(reset_pytest_airflow_vars, capfd):
    """Test that the DAG's task runs through successfully"""
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # run the task and retrive the terminal output in an airflow context
    task = reset_dag_configs.reset_dag_configs_task
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())
    out, err = capfd.readouterr()

    expected_result = f"Airflow Variables within {reset_dag_configs_generator.reset_configs_in_scope_list} are now reset based on files in this location: {reset_dag_configs_generator.reset_configs_directory_in_scope}"
    assert expected_result in out.strip("\n")


def test_end_to_end_pipeline(reset_pytest_airflow_vars, get_test_configs):
    """
    Runs the DAG end to end in cloud composer
    The end to end test is distinct from the other tests as this ensures the whole DAG runs in cloud composer successfully
    The other tests focus on component functionality within a local airflow environment as it is not feasible to do so within cloud composer at this time
    """
    # set the pytest variables
    reset_dag_configs_generator = reset_pytest_airflow_vars

    # define the project and bucket to upload dag and config files for cloud composer testing
    test_configs = get_test_configs
    project_id = test_configs.get("project_id")
    bucked_id = test_configs.get("bucked_id")
    cloud_composer_id = test_configs.get("cloud_composer_id")

    # ensures correct permissions are used
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/account.json"

    # upload dag to cloud storage bucket for cloud composer
    client = storage.Client(project=project_id)
    bucket = client.get_bucket(bucked_id)
    file_location_dag = "/pytest/dags/reset_dag_configs.py"
    blob_dag = bucket.blob("dags/" + "reset_dag_configs.py")
    blob_dag.upload_from_filename(file_location_dag)

    # upload reset_dag_configs_{ENVIRONMENT_CONFIG}.json into cloud storage bucket for cloud composer
    file_location_config = f"/pytest/dag_environment_configs/{ENVIRONMENT_CONFIG}/reset_dag_configs_{ENVIRONMENT_CONFIG}.json"
    blob_config = bucket.blob(
        "data/dag_environment_configs/{ENVIRONMENT_CONFIG}/"
        + "reset_dag_configs_{ENVIRONMENT_CONFIG}.json"
    )
    blob_config.upload_from_filename(file_location_config)

    # upload pipeline configs in scope to cloud storage bucket for cloud composer
    for config_file in reset_dag_configs_generator.reset_configs_in_scope_list:
        file_location = (
            reset_dag_configs_generator.reset_configs_directory_in_scope + config_file
        )
        blob = bucket.blob(
            f"data/dag_environment_configs/{ENVIRONMENT_CONFIG}/" + config_file
        )
        blob.upload_from_filename(file_location)

    # gcloud command to import variables into cloud composer
    command = f"gcloud composer environments run {cloud_composer_id} variables -- --import /home/airflow/gcsfuse/dag_environment_configs/{ENVIRONMENT_CONFIG}/reset_dag_configs_{ENVIRONMENT_CONFIG}.json"
    process = subprocess.run(command.split())
    assert process.returncode == 0  # should be 0

    # wait 40 seconds for cloud composer to update the DAG within the database
    time.sleep(40)

    # run the the full pipeline without errors
    command = f"gcloud composer environments run {cloud_composer_id} test -- reset_dag_configs reset_dag_configs_task 2020-01-02"
    process = subprocess.run(command.split())
    assert process.returncode == 0  # should be 0
