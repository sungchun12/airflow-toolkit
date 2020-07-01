import pytest
from airflow.models import DagBag, TaskInstance
from datetime import datetime
import subprocess
import time
import os

# import created modules
import dags.add_gcp_connection as add_gcp_connection_dag
import dags.adhoc_pipeline as pilot_pipeline # needs to be updated to DAG being tested
import tests.gcp_utilities as gcp_utilities
from airflow.models import Variable
from airflow.exceptions import AirflowSensorTimeout
import json
from airflow import DAG, settings
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


"""Tests the airflow commands and verifies 
successful connections to the proper environments
"""

# Global Vars
PIPELINE = "adhoc_pipeline"  # DAG to be tested. pilot_pipeline import above also need to be updated to this
PROJECT_NAME = os.environ["DBT_DATABASE"].lower()  # GCP project where BQ resides
ENVIRONMENT = os.environ["ENV"].lower()

DEFAULT_ARGS = Variable.get(f"{PIPELINE}_default_args", deserialize_json=True)
RUNTIME_PARAMETERS = Variable.get(
    f"{PIPELINE}_runtime_parameters", deserialize_json=True
)
JSON_TABLES_IN_SCOPE_LIST = Variable.get(
    f"{PIPELINE}_json_tables", deserialize_json=True
)
CSV_TABLES_IN_SCOPE_LIST = Variable.get(f"{PIPELINE}_csv_tables", deserialize_json=True)
DBT_COMMANDS = Variable.get(f"{PIPELINE}_dbt_commands", deserialize_json=True)

GCS_BUCKET = DEFAULT_ARGS["bucket"]

TRANSFER_LIST = JSON_TABLES_IN_SCOPE_LIST + CSV_TABLES_IN_SCOPE_LIST

test_configs = {
    "project_name": PROJECT_NAME,
    "dataset_name": f"test_PYTEST_{PIPELINE}",
    "dataset_location": "us-east4",
    "raw_data_bucket": GCS_BUCKET,
    "raw_data_bucket_path": f"unit_test_archive/raw_data/{PIPELINE}/",
    "raw_schemas_bucket_path": "unit_test_archive/schemas/",
    "success_path": f"unit_test_archive/raw_data/{PIPELINE}/success/",
    "error_path": f"unit_test_archive/raw_data/{PIPELINE}/error/",
}

# initialize gcp_utilities with test_configs values
gcp_toolkit = gcp_utilities.gcp_utilities(test_configs)

# copy json files from unit_test_archive to pipeline subfolder
for table in JSON_TABLES_IN_SCOPE_LIST:
    gcp_toolkit.copy_single_file_gcs_to_gcs(
        bucket_name=test_configs["raw_data_bucket"],
        blob_name="unit_test_archive/" + table + ".json",
        destination_bucket_name=test_configs["raw_data_bucket"],
        destination_blob_name=test_configs["raw_data_bucket_path"] + table + ".json",
    )

# copy csv files from unit_test_archive to pipeline subfolder
for table in CSV_TABLES_IN_SCOPE_LIST:
    gcp_toolkit.copy_single_file_gcs_to_gcs(
        bucket_name=test_configs["raw_data_bucket"],
        blob_name="unit_test_archive/" + table + ".csv",
        destination_bucket_name=test_configs["raw_data_bucket"],
        destination_blob_name=test_configs["raw_data_bucket_path"] + table + ".csv",
    )


@pytest.fixture
def setup_method():
    """ setup any state specific to the execution of the given class (which
    usually contains tests).
    """
    dag_folder = "/pytest/dags/"
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
            f"{PIPELINE}_json_tables",
            json.dumps(json_object[f"{PIPELINE}_json_tables"]),
        )
        Variable.set(
            f"{PIPELINE}_csv_tables", json.dumps(json_object[f"{PIPELINE}_csv_tables"]),
        )
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


# https://www.linkedin.com/pulse/dynamic-workflows-airflow-kyle-bridenstine
# resetting task status is a known bug, so we have to draft more drawn out logic to test failures dependent on Airflow Variables
def test_fail_raw_data_sensor_task(setup_method, reset_pytest_airflow_vars):
    "Timeout feature should display a AirflowSensorTimeout exception"
    try:
        # set the json table in scope to a fake table
        timeout_table = ["timeout"]
        timeout_table_json = json.dumps(timeout_table)
        Variable.set(f"{PIPELINE}_json_tables", timeout_table_json)

        # recreate the utilities after updating the variables
        dynamic_task_generator = pilot_pipeline.dynamic_task_generator_utility()
        default_args = dynamic_task_generator.default_args

        # create a completely separate dag during test runtime
        with DAG(
            "test_timeout", default_args=default_args, schedule_interval=None
        ) as dag:
            all_sensor_tasks_list = dynamic_task_generator.create_all_sensor_tasks()

        dag_folder = "/pytest/dags/"
        setup_dagbag = DagBag(dag_folder=dag_folder)

        # define the task id to find
        task_id_to_find = "timeout_raw_data_sensor"

        # find it in the list
        task = next(
            (task for task in all_sensor_tasks_list if task.task_id == task_id_to_find),
            None,
        )

        # execute the task
        ti = TaskInstance(task=task, execution_date=datetime.now())
        task.execute(ti.get_template_context())
        assert False
    except AirflowSensorTimeout:
        assert True

    reset_pytest_airflow_vars


def test_dag_environment_configs(reset_pytest_airflow_vars):
    """Test programatically setting the dag configs matches JSON file contents
    """

    with open(
        "/pytest/dag_environment_configs/dag_config_pytest_dummy.json", "r"
    ) as openfile:
        # read in the file
        json_object = json.load(openfile)

        # set the airflow variables
        Variable.set(
            "json_tables_in_scope_list",
            json.dumps(json_object["json_tables_in_scope_list"]),
        )
        Variable.set(
            "csv_tables_in_scope_list",
            json.dumps(json_object["csv_tables_in_scope_list"]),
        )
        Variable.set(
            "runtime_parameters", json.dumps(json_object["runtime_parameters"])
        )
        Variable.set("default_args", json.dumps(json_object["default_args"]))

        # get the airflow variables
        get_json_tables_in_scope_list = Variable.get(
            "json_tables_in_scope_list", deserialize_json=True
        )
        get_csv_tables_in_scope_list = Variable.get(
            "csv_tables_in_scope_list", deserialize_json=True
        )
        get_runtime_parameters = Variable.get(
            "runtime_parameters", deserialize_json=True
        )
        get_default_args = Variable.get("default_args", deserialize_json=True)

        # match contents of JSON across each one
        assert json_object["json_tables_in_scope_list"] == get_json_tables_in_scope_list
        assert json_object["csv_tables_in_scope_list"] == get_csv_tables_in_scope_list
        assert json_object["runtime_parameters"] == get_runtime_parameters
        assert json_object["default_args"] == get_default_args

        # delete the airflow variables to cleanup
        Variable.delete("json_tables_in_scope_list")
        Variable.delete("csv_tables_in_scope_list")
        Variable.delete("runtime_parameters")
        Variable.delete("default_args")

    reset_pytest_airflow_vars


def test_import_dags(setup_method, reset_pytest_airflow_vars):
    """Test the dags imported have no syntax errors
    """
    reset_pytest_airflow_vars
    dag_errors_message = len(setup_method.import_errors)
    assert dag_errors_message == 0


# TODO: move out into separate test file for add_gcp_connection dag?
def test_task_count_add_gcp_connection(setup_method, reset_pytest_airflow_vars):
    """Check task count of add_gcp_connection dag"""
    reset_pytest_airflow_vars
    dag_id = "add_gcp_connection"
    dag = setup_method.get_dag(dag_id)
    dag_task_count = len(dag.tasks)
    result = 2
    assert dag_task_count == result


def test_task_count_pilot_pipeline(setup_method, reset_pytest_airflow_vars):
    """Check task count of demo_pilot_pipeline dag"""
    reset_pytest_airflow_vars
    dag_id = pilot_pipeline.dag.dag_id
    dag = setup_method.get_dag(dag_id)
    dag_task_count = len(dag.tasks)

    # create_empty_dataset_if_needed, branch_task, dbt_proceed_check, dbt_debug
    static_expected_task_count = 4
    # all_sensor_tasks_list, gcs_to_bq_task_list, success_gcs_to_gcs_task_list, error_gcs_to_gcs_task_list
    dynamic_expected_task_count = len(TRANSFER_LIST) * 5
    # dbt commands
    dbt_expected_task_count = len(DBT_COMMANDS)
    total_expected_task_count = (
        static_expected_task_count
        + dynamic_expected_task_count
        + dbt_expected_task_count
    )

    assert dag_task_count == total_expected_task_count


# parameter for looping test
@pytest.mark.parametrize("table_name", TRANSFER_LIST)
def test_gcs_to_bq_tasks(table_name, reset_pytest_airflow_vars):
    """Test airflow can load an existing file from gcs into an existing bq table
    """
    reset_pytest_airflow_vars

    # Create empty dataset if it doesn't exist
    gcp_toolkit.create_bigquery_dataset()

    # delete the table if it already exists
    gcp_toolkit.delete_bigquery_table(table_name)

    # define the task id to find
    task_id_to_find = f"{table_name}_transfer"
    # find it in the list
    task = next(
        (
            task
            for task in pilot_pipeline.gcs_to_bq_task_list
            if task.task_id == task_id_to_find
        ),
        None,
    )
    # execute the task
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())

    # check if the table exists in bigquery
    assert gcp_toolkit.validate_bigquery_table_exists(table_name) == True

    # delete test dataset
    gcp_toolkit.delete_bigquery_dataset()


@pytest.mark.parametrize("table_name", JSON_TABLES_IN_SCOPE_LIST)
@pytest.mark.parametrize("transfer_type", ["success", "error"])
def test_json_gcs_to_gcs_tasks(table_name, transfer_type, reset_pytest_airflow_vars):
    """Test airflow can move a file from one gcs location to another
    """
    reset_pytest_airflow_vars

    if transfer_type == "success":
        # set path to bucket
        bucket_path = test_configs["raw_data_bucket"]
        # set path to file
        file_path = (
            test_configs["success_path"] + f"{table_name}/" + table_name + ".json"
        )
        # delete processed file if it already exists
        try:
            gcp_toolkit.delete_blob(bucket_path, file_path)
        except:
            print(f"{file_path} didn't exist, no need to delete")
        # define the task id to find for processed files
        task_id_to_find = f"{table_name}_move_processed_file"
        # find it in the list
        task = next(
            (
                task
                for task in pilot_pipeline.success_gcs_to_gcs_task_list
                if task.task_id == task_id_to_find
            ),
            None,
        )
        # execute the task
        ti = TaskInstance(task=task, execution_date=datetime.now())
        task.execute(ti.get_template_context())

        # check if the file exists in gcs bucket_path
        print(bucket_path + file_path)
        assert gcp_toolkit.validate_gcs_file_exists(bucket_path, file_path) == True

        # move file back to original folder
        gcp_toolkit.move_single_file_gcs_to_gcs(
            bucket_name=bucket_path,
            blob_name=file_path,
            destination_bucket_name=bucket_path,
            destination_blob_name=test_configs["raw_data_bucket_path"]
            + table_name
            + ".json",
        )

    if transfer_type == "error":
        # set path to bucket
        bucket_path = test_configs["raw_data_bucket"]
        # set path to file
        file_path = test_configs["error_path"] + table_name + ".json"
        # delete processed file if it already exists
        try:
            gcp_toolkit.delete_blob(bucket_path, file_path)
        except:
            print(f"{file_path} didn't exist, no need to delete")
        # define the task id to find for processed files
        task_id_to_find = f"{table_name}_move_error_file"
        # find it in the list
        task = next(
            (
                task
                for task in pilot_pipeline.error_gcs_to_gcs_task_list
                if task.task_id == task_id_to_find
            ),
            None,
        )
        # execute the task
        ti = TaskInstance(task=task, execution_date=datetime.now())
        task.execute(ti.get_template_context())

        # check if the file exists in gcs bucket_path
        assert gcp_toolkit.validate_gcs_file_exists(bucket_path, file_path) == True

        # move file back to original folder
        gcp_toolkit.move_single_file_gcs_to_gcs(
            bucket_name=bucket_path,
            blob_name=file_path,
            destination_bucket_name=bucket_path,
            destination_blob_name=test_configs["raw_data_bucket_path"]
            + table_name
            + ".json",
        )


@pytest.mark.parametrize("table_name", CSV_TABLES_IN_SCOPE_LIST)
@pytest.mark.parametrize("transfer_type", ["success", "error"])
def test_csv_gcs_to_gcs_tasks(table_name, transfer_type, reset_pytest_airflow_vars):
    """Test airflow can move a file from one gcs location to another
    """
    reset_pytest_airflow_vars

    if transfer_type == "success":
        # set path to bucket
        bucket_path = test_configs["raw_data_bucket"]
        # set path to file
        file_path = (
            test_configs["success_path"] + f"{table_name}/" + table_name + ".csv"
        )
        # delete processed file if it already exists
        try:
            gcp_toolkit.delete_blob(bucket_path, file_path)
        except:
            print(f"{file_path} didn't exist, no need to delete")
        # define the task id to find for processed files
        task_id_to_find = f"{table_name}_move_processed_file"
        # find it in the list
        task = next(
            (
                task
                for task in pilot_pipeline.success_gcs_to_gcs_task_list
                if task.task_id == task_id_to_find
            ),
            None,
        )
        # execute the task
        ti = TaskInstance(task=task, execution_date=datetime.now())
        task.execute(ti.get_template_context())

        # check if the file exists in gcs bucket_path
        assert gcp_toolkit.validate_gcs_file_exists(bucket_path, file_path) == True

        # move file back to original folder
        gcp_toolkit.move_single_file_gcs_to_gcs(
            bucket_name=bucket_path,
            blob_name=file_path,
            destination_bucket_name=bucket_path,
            destination_blob_name=test_configs["raw_data_bucket_path"]
            + table_name
            + ".csv",
        )

    if transfer_type == "error":
        # set path to bucket
        bucket_path = test_configs["raw_data_bucket"]
        # set path to file
        file_path = test_configs["error_path"] + table_name + ".csv"
        # delete processed file if it already exists
        try:
            gcp_toolkit.delete_blob(bucket_path, file_path)
        except:
            print(f"{file_path} didn't exist, no need to delete")
        # define the task id to find for processed files
        task_id_to_find = f"{table_name}_move_error_file"
        # find it in the list
        task = next(
            (
                task
                for task in pilot_pipeline.error_gcs_to_gcs_task_list
                if task.task_id == task_id_to_find
            ),
            None,
        )
        # execute the task
        ti = TaskInstance(task=task, execution_date=datetime.now())
        task.execute(ti.get_template_context())

        # check if the file exists in gcs bucket_path
        assert gcp_toolkit.validate_gcs_file_exists(bucket_path, file_path) == True

        # move file back to original folder
        gcp_toolkit.move_single_file_gcs_to_gcs(
            bucket_name=bucket_path,
            blob_name=file_path,
            destination_bucket_name=bucket_path,
            destination_blob_name=test_configs["raw_data_bucket_path"]
            + table_name
            + ".csv",
        )


@pytest.mark.parametrize("table_name", TRANSFER_LIST)
@pytest.mark.timeout(5)
def test_raw_data_sensor_tasks(table_name, reset_pytest_airflow_vars):
    "If it takes longer than 30 seconds to finish finding the file, the file doesn't exist"
    reset_pytest_airflow_vars
    # define the task id to find
    task_id_to_find = f"{table_name}_raw_data_sensor"
    # find it in the list
    task = next(
        (
            task
            for task in pilot_pipeline.all_sensor_tasks_list
            if task.task_id == task_id_to_find
        ),
        None,
    )
    # execute the task
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())


@pytest.mark.parametrize("table_name", TRANSFER_LIST)
@pytest.mark.timeout(5)
def test_schema_sensor_tasks(table_name, reset_pytest_airflow_vars):
    "If it takes longer than 30 seconds to finish finding the file, the file doesn't exist"
    reset_pytest_airflow_vars
    # define the task id to find
    task_id_to_find = f"{table_name}_schema_sensor"
    # find it in the list
    task = next(
        (
            task
            for task in pilot_pipeline.all_sensor_tasks_list
            if task.task_id == task_id_to_find
        ),
        None,
    )
    # execute the task
    ti = TaskInstance(task=task, execution_date=datetime.now())
    task.execute(ti.get_template_context())


def test_gcp_connection(capfd):
    """Test creating a new Google Cloud connection through a service account file in the airflow directory
    Must include the service account within the tests folder as of now
    """
    expected_result = [
        "\n\tA connection with `conn_id`=my_gcp_connection is newly created\n\n",
        "\n\tA connection with `conn_id`=my_gcp_connection already exists\n\n",
    ]
    try:
        # dag = add_gcp_connection_dag.dag
        task = add_gcp_connection_dag.t1
        ti = TaskInstance(task=task, execution_date=datetime.now())
        result = task.execute(ti.get_template_context())
        out, err = capfd.readouterr()
        assert out == expected_result[0]
    except AssertionError:
        assert out == expected_result[1]


def test_docker_registry_connection(capfd):
    """Test creating a new Google Cloud Docker Registry connection through a service account file in the airflow directory
    Must include the service account within the tests folder as of now
    """
    expected_result = [
        "\n\tA connection with `conn_id`=gcr_docker_connection is newly created\n\n",
        "\n\tA connection with `conn_id`=gcr_docker_connection already exists\n\n",
    ]
    try:
        # dag = add_gcp_connection_dag.dag
        task = add_gcp_connection_dag.t2
        ti = TaskInstance(task=task, execution_date=datetime.now())
        result = task.execute(ti.get_template_context())
        out, err = capfd.readouterr()
        assert out == expected_result[0]
    except AssertionError:
        assert out == expected_result[1]


def test_update_bigquery_dataset_desc(reset_pytest_airflow_vars):
    """Test that the bigquery dataset description matches what the function creates
    """
    reset_pytest_airflow_vars

    # Create empty dataset if it doesn't exist using the utility
    gcp_toolkit.create_bigquery_dataset()

    # message to update
    updated_description = "test_desc"

    # run the function
    pilot_pipeline.dynamic_task_generator.update_bigquery_dataset_desc(
        updated_description
    )

    # check if the descriptions match
    bigquery_client = bigquery.Client(
        RUNTIME_PARAMETERS["destination_project_dataset"].split(":")[0]
    )
    dataset_id = RUNTIME_PARAMETERS["destination_project_dataset"].replace(":", ".")
    dataset = bigquery_client.get_dataset(dataset_id)
    assert dataset.description == updated_description

    # delete test dataset
    gcp_toolkit.delete_bigquery_dataset()


def test_create_bigquery_dataset(reset_pytest_airflow_vars):
    """Test it handles creating a bigquery dataset whether it exists or not
    """
    reset_pytest_airflow_vars
    # expected result
    expected_result = "Dataset(DatasetReference('{}', '{}'))".format(
        test_configs["project_name"], test_configs["dataset_name"]
    )
    try:
        # run the function
        pilot_pipeline.dynamic_task_generator.create_bigquery_dataset()

        # assert if the dataset actually exists
        bigquery_client = bigquery.Client(
            RUNTIME_PARAMETERS["destination_project_dataset"].split(":")[0]
        )
        dataset_id = RUNTIME_PARAMETERS["destination_project_dataset"].replace(":", ".")
        result = str(bigquery_client.get_dataset(dataset_id))
        assert result == expected_result
    except NotFound:
        assert False

    # delete test dataset
    gcp_toolkit.delete_bigquery_dataset()


def test_create_empty_dataset_if_needed_task(reset_pytest_airflow_vars):
    """Test that the function executes successfully
    """
    reset_pytest_airflow_vars
    # expected result
    expected_result = "Dataset(DatasetReference('{}', '{}'))".format(
        test_configs["project_name"], test_configs["dataset_name"]
    )
    try:
        task = getattr(
            pilot_pipeline, "create_empty_dataset_if_needed"
        )  # dynamically call attribute function call
        ti = TaskInstance(task=task, execution_date=datetime.now())
        task.execute(ti.get_template_context())
        # assert if the dataset actually exists
        bigquery_client = bigquery.Client(
            RUNTIME_PARAMETERS["destination_project_dataset"].split(":")[0]
        )
        dataset_id = RUNTIME_PARAMETERS["destination_project_dataset"].replace(":", ".")
        result = str(bigquery_client.get_dataset(dataset_id))
        assert result == expected_result
    except NotFound:
        assert False

    # delete test dataset
    gcp_toolkit.delete_bigquery_dataset()


# TODO: update end to end test to run on cloud composer
def test_branch_and_dbt_proceed_tasks(reset_pytest_airflow_vars):
    """ Run pipeline with known failure scenario to compare
        branch and dbt_proceed_check task expected outcomes.
        Success scenarios are covered by test_pipeline_end_to_end test
    """
    # reset variables used by airflow
    reset_pytest_airflow_vars

    # Create empty dataset if it doesn't exist using the utility
    gcp_toolkit.create_bigquery_dataset()

    # delete known good file
    gcp_toolkit.delete_blob(
        test_configs["raw_data_bucket"], 
        test_configs["raw_data_bucket_path"] + "assortment.json"
    )

    # copy known error file needed for testing to raw_data folder
    gcp_toolkit.copy_single_file_gcs_to_gcs(
        bucket_name=test_configs["raw_data_bucket"],
        blob_name="unit_test_archive/assortment_error.json",
        destination_bucket_name=test_configs["raw_data_bucket"],
        destination_blob_name=test_configs["raw_data_bucket_path"]
        + "assortment_error.json",
    )

    # copy csv files needed for testing to raw_data folder
    for table in CSV_TABLES_IN_SCOPE_LIST:
        gcp_toolkit.copy_single_file_gcs_to_gcs(
            bucket_name=test_configs["raw_data_bucket"],
            blob_name="unit_test_archive/" + table + ".csv",
            destination_bucket_name=test_configs["raw_data_bucket"],
            destination_blob_name=test_configs["raw_data_bucket_path"] + table + ".csv",
        )

    # run pipeline and capture the output
    command = f"airflow backfill {PIPELINE} -s 2020-01-01 -e 2020-01-02 --subdir /pytest/dags/ --reset_dagruns -y -l"
    process = subprocess.run(command.split(), capture_output=True, text=True)

    # if the returncode is 1 then the pipeline failed as expected
    if process.returncode == 1:
        # validate that known error file was moved to error folder.
        # hard coded assortment file because test configs remain consistent for pytest operations.
        assert gcp_toolkit.validate_gcs_file_exists(
                    test_configs["raw_data_bucket"],
                    test_configs["error_path"] + "assortment_error.json"
                ) == True

        # validate that dbt_proceed_check stopped dbt tasks from running.
        for table in TRANSFER_LIST:
            # check that table doesn't exist in bigquery
            assert gcp_toolkit.validate_bigquery_table_exists("test_" + table) == False

    # cleanup
    # delete test dataset
    gcp_toolkit.delete_bigquery_dataset()

    # delete error file
    gcp_toolkit.delete_blob(
        test_configs["raw_data_bucket"], 
        test_configs["error_path"] + "assortment_error.json"
    )
    

# TODO: update end to end test to run on cloud composer
def test_pipeline_end_to_end(reset_pytest_airflow_vars):
    """ Run pipeline and test that we get the expected outputs from known
        input files. This will primarily be checked by comparing row counts
        between staging and source tables.
    """
    # reset variables used by airflow
    reset_pytest_airflow_vars

    # Create empty dataset if it doesn't exist using the utility
    gcp_toolkit.create_bigquery_dataset()

    # copy json files needed for testing to raw_data folder
    for table in JSON_TABLES_IN_SCOPE_LIST:
        gcp_toolkit.copy_single_file_gcs_to_gcs(
            bucket_name=test_configs["raw_data_bucket"],
            blob_name="unit_test_archive/" + table + ".json",
            destination_bucket_name=test_configs["raw_data_bucket"],
            destination_blob_name=test_configs["raw_data_bucket_path"]
            + table
            + ".json",
        )

    # copy csv files needed for testing to raw_data folder
    for table in CSV_TABLES_IN_SCOPE_LIST:
        gcp_toolkit.copy_single_file_gcs_to_gcs(
            bucket_name=test_configs["raw_data_bucket"],
            blob_name="unit_test_archive/" + table + ".csv",
            destination_bucket_name=test_configs["raw_data_bucket"],
            destination_blob_name=test_configs["raw_data_bucket_path"] + table + ".csv",
        )

    # run pipeline twice to test idempotency
    for _ in range(2):
        try:
            # run airflow backfill command and capture the output
            command = f"airflow backfill {PIPELINE} -s 2020-01-01 -e 2020-01-02 --subdir /pytest/dags/ --reset_dagruns -y -l"
            process = subprocess.run(command.split(), capture_output=True, text=True)
        except Exception as e:
            print(e)

        # move json files back to original location for second pipeline run
        for table in JSON_TABLES_IN_SCOPE_LIST:
            gcp_toolkit.move_single_file_gcs_to_gcs(
                bucket_name=test_configs["raw_data_bucket"],
                blob_name=test_configs["success_path"] + f"{table}/" + table + ".json",
                destination_bucket_name=test_configs["raw_data_bucket"],
                destination_blob_name=test_configs["raw_data_bucket_path"]
                + table
                + ".json",
            )

        # move csv files back to original location for second pipeline run
        for table in CSV_TABLES_IN_SCOPE_LIST:
            gcp_toolkit.move_single_file_gcs_to_gcs(
                bucket_name=test_configs["raw_data_bucket"],
                blob_name=test_configs["success_path"] + f"{table}/" + table + ".csv",
                destination_bucket_name=test_configs["raw_data_bucket"],
                destination_blob_name=test_configs["raw_data_bucket_path"]
                + table
                + ".csv",
            )

    # print commands useful for debugging subprocess run above, will only show if test fails
    print(f"the process (dag run) stderr is {process.stderr}")
    print(f"the process (dag run) return code is {process.returncode}")

    # if the returncode is zero then the pipeline exited with no errors
    if process.returncode == 0:
        # set project and dataset
        project_name = test_configs["project_name"]
        dataset = test_configs["dataset_name"]

        # count of staging and source tables with mismatches
        mismatch_count = 0

        # create bigquery client object
        client = bigquery.Client()

        # loop through list of tables and get row counts for staging and source
        for table in TRANSFER_LIST:
            staging_query = f"""
                SELECT COUNT(*) as count
                FROM `{project_name}.{dataset}.{table}`
            """
            source_query = f"""
                SELECT COUNT(*) as count
                FROM `{project_name}.{dataset}.test_{table}_{PIPELINE}`
            """

            # make API calls to run queries
            staging_query_job = client.query(staging_query)
            source_query_job = client.query(source_query)

            # get query results
            for row in staging_query_job:
                staging_count = row["count"]
            for row in source_query_job:
                source_count = row["count"]

            # if counts aren't equal increment mismatch_count
            if staging_count != source_count:
                mismatch_count += 1

        # if no mismatches, test passes
        assert mismatch_count == 0

        # delete test dataset
        gcp_toolkit.delete_bigquery_dataset()

    elif process.returncode == 1:
        pytest.fail("pipeline did not run successfully. failing test.")


# TODO: Below dbt tests may be refactored later to work in cloud composer. Currently not needed since
#       dbt tasks are run in pipeline end to end test.
# dbt_task_list = [
#     "dbt_deps",
#     "dbt_debug",
#     "dbt_source_freshness",
#     "dbt_test_staging",
#     "dbt_run",
#     "dbt_test_transformed",
# ]
# # TODO(developer): airflow tests will NOT overwrite existing staging tables. These simply test if all dbt tasks run through successfully.# @pytest.mark.parametrize("dbt_task", dbt_task_list)
# @pytest.mark.parametrize("dbt_task", dbt_task_list)
# def test_dbt_tasks(dbt_task, reset_pytest_airflow_vars):
#     "Tests that dbt tasks in scope operate as expected"
#     reset_pytest_airflow_vars
#     task = getattr(pilot_pipeline, dbt_task)  # dynamically call attribute function call
#     ti = TaskInstance(task=task, execution_date=datetime.now())
#     task.execute(ti.get_template_context())