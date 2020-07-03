"""
Resets DAG configs everyday to enforce consistency before automated pipelines in scope are scheduled to run

ENV: dev, qa, prod

Assumes configuration json files are already stored within the cloud composer, google cloud storage directory: `/home/airflow/gcsfuse/data/dag_environment_configs/<ENV>/`

Jenkins will deploy all relevant files in QA and PROD

This can dynamically extend one to many configs

Relies on a config file: `reset_dag_configs_<ENV>.json`
"""

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python_operator import PythonOperator
import json
from collections import Counter
import sys


class reset_dag_configs_utility:
    """A set of dynamic airflow variable reset tasks
    """

    # get the airflow variables for json config in scope
    # assumes variables were already imported into airflow variables before this is invoked
    def __init__(self):
        self.reset_configs_default_args = Variable.get(
            "reset_configs_default_args", deserialize_json=True
        )
        self.reset_configs_in_scope_list = Variable.get(
            "reset_configs_in_scope_list", deserialize_json=True
        )
        self.reset_configs_directory_in_scope = Variable.get(
            "reset_configs_directory_in_scope", deserialize_json=True
        )
        # extract the value as a string from the list object
        self.reset_configs_directory_in_scope = self.reset_configs_directory_in_scope[0]

    def reset_dag_configs(self):
        """Main interface for running class utility.
        Thi can be extended over time without changing downstream PythonOperator logic.
        """
        self.validate_no_duplicate_config_vars()
        self.set_dag_configs()
        self.get_dag_configs()
        print(
            f"Airflow Variables within {self.reset_configs_in_scope_list} are now reset based on files in this location: {self.reset_configs_directory_in_scope}"
        )

    def validate_no_duplicate_config_vars(self):
        """Verify the literal file contents do NOT have duplicate variable names before uploading them as Airflow Variables
        """
        # dynamically locate and open the files in order to store variable names
        config_variables_list = []
        for config_file in self.reset_configs_in_scope_list:
            file_location = self.reset_configs_directory_in_scope + config_file

            with open(file_location, "r") as openfile:
                # read in the file
                json_object = json.load(openfile)
                variable_names = json_object.keys()
                # append to list
                [config_variables_list.append(var) for var in variable_names]

        # isolate duplicate variable names
        print(f"Airflow Variables to be uploaded: {config_variables_list}")
        d = Counter(config_variables_list)
        result = [k for k, v in d.items() if v > 1]
        if not result:
            print(
                f"There are no duplicate variables within {self.reset_configs_in_scope_list} based on files in this location: {self.reset_configs_directory_in_scope}"
            )
        else:
            print(
                f"These are the duplicate variables {result} within {self.reset_configs_in_scope_list} based on files in this location: {self.reset_configs_directory_in_scope}"
            )
            sys.exit("Stopping the DAG now!")

    def set_dag_configs(self):
        """Programatically set the DAG configs into the Airflow Variables
        """
        # dynamically locate and open the files
        for config_file in self.reset_configs_in_scope_list:
            file_location = self.reset_configs_directory_in_scope + config_file

            with open(file_location, "r") as openfile:
                # read in the file
                json_object = json.load(openfile)

                # grab the keys from the json_object to dynamically get the variable name
                [
                    Variable.set(key, json.dumps(json_object[key], indent=4),)
                    for key in json_object.keys()
                ]
        print("Uploaded Airflow Variables")

    def get_dag_configs(self):
        """Test uploaded Airflow Variables match JSON file literal contents
        """
        # loop through all the config files
        # open actual file contents and assert they match parsed out retrieval from airflow variables
        for config_file in self.reset_configs_in_scope_list:
            file_location = self.reset_configs_directory_in_scope + config_file

            with open(file_location, "r") as openfile:
                json_object = json.load(openfile)  # read in the file

                # get the airflow variables in dict comprehension
                airflow_variables = {
                    k: Variable.get(k, deserialize_json=True)
                    for k, v in json_object.items()
                }

                # match contents of config file across each airflow variable
                for key in json_object.keys():
                    assert json_object[key] == airflow_variables[key]

        print("Validated Airflow Variables match config file contents")


# define the utility
reset_dag_configs_generator = reset_dag_configs_utility()

with DAG(
    "reset_dag_configs",
    default_args=reset_dag_configs_generator.reset_configs_default_args,
    schedule_interval=None,  # 7am Eastern time is 11am UTC, scheduled daily, serves as a placeholder schedule
) as dag:
    # a single task regardless of how many configs are being reset
    reset_dag_configs_task = PythonOperator(
        task_id="reset_dag_configs_task",
        python_callable=reset_dag_configs_generator.reset_dag_configs,
    )


reset_dag_configs_task
