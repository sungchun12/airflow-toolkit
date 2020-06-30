from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
import json
from airflow.models import Variable
import os
from airflow.utils.helpers import chain
from airflow.contrib.kubernetes.secret import Secret
from airflow.operators.dummy_operator import DummyOperator
from airflow import configuration as conf

namespace = conf.get('kubernetes', 'NAMESPACE')

# This will detect the default namespace locally and read the 
# environment namespace when deployed to Astronomer.
if namespace =='airflow':
    config_file = '/home/airflow/.kube/config'
    in_cluster=False
else:
    in_cluster=True
    config_file=None

"""
Runs a set of dbt commands with the KubernetesPodOperator on Cloud Composer.

Ad hoc workflow
export PROJECT_DIR=$PWD
export GCP_PROJECT="gcp-ushi-daci-npe"
COMPOSER_ENVIRONMENT="dacipoccomposer"
gcloud config set composer/location us-east4
COMPOSER_BUCKET=$(gcloud composer environments describe ${COMPOSER_ENVIRONMENT} --format='value(config.dagGcsPrefix)' | sed 's/\/dags//g')

# Copy single DAG
gsutil cp $PROJECT_DIR/airflow_LOCAL_setup/dags/dbt_kube_dag.py $COMPOSER_BUCKET/dags/

# Copy other config files
gsutil cp $PROJECT_DIR/Docker/account.json $COMPOSER_BUCKET/data/dag_environment_configs/dev/account.json

# Copy single config
gsutil cp $PROJECT_DIR/airflow_LOCAL_setup/dag_environment_configs/dev/dbt_kube_config_dev_pytest.json $COMPOSER_BUCKET/dag_environment_configs/dev/

# Import the config file
gcloud composer environments run $COMPOSER_ENVIRONMENT variables -- --import /home/airflow/gcsfuse/dag_environment_configs/dev/dbt_kube_config_dev_pytest.json

# See if the variable updated
gcloud composer environments run $COMPOSER_ENVIRONMENT variables -- --get default_args

#trigger the example DAG OR run manually from the UI
# https://k86e12c660d696f8b-tp.appspot.com/admin/

# run dbt commands on the VM
export dbt_IMG=gcr.io/gcp-ushi-daci-npe/dbt_docker:dev-schung-latest
export SERVICE_ACCOUNT="test"
export SERVICE_ACCOUNT=$(gcloud secrets versions access latest --secret="SERVICE_ACCOUNT" --project=gcp-ushi-daci-npe)
docker run --rm -it \
    --env-file ${PROJECT_DIR}/Docker/dbt/dbt.env \
    $dbt_IMG \
    dbt debug


# these permissions must be in place for service account attached to the VM that connects to Cloud Composer
container.secrets.create	SUPPORTED
container.secrets.delete	SUPPORTED
container.secrets.get	SUPPORTED
container.secrets.list	SUPPORTED
container.secrets.update	SUPPORTED

# can possibly create another service account only allowed to invoke this outside of automated process service accounts
# create a secret from file directly into kubernetes cluster hosting cloud composer
kubectl create secret generic dbt-secret --from-file=account.json

# view encrypted secret, it will NOT appear as plain text
kubectl get secret dbt-secret -o yaml

# delete a secret
kubectl delete secret dbt-secret

# Cloud Composer GKE information
GKE_CLUSTER=$(gcloud composer environments describe <composer_name> --format='value(config.gkeCluster)')
GKE_LOCATION="us-east4-a"
gcloud container clusters get-credentials ${GKE_CLUSTER} --zone ${GKE_LOCATION}
"""

# TODO: Separate dynamic_task_generator_utility out to its own file.
class dynamic_task_generator_utility:
    """A set of dynamic airflow task generators for dbt in the kubernetes
    """

    def __init__(self):
        self.default_args = Variable.get(
            "dbt_kube_dag_default_args", deserialize_json=True
        )
        self.runtime_parameters = Variable.get(
            "dbt_kube_dag_runtime_parameters", deserialize_json=True
        )

        # Variable.get() uses json.load()
        # which silently overwrites duplicate/identitcal keys.
        # In other words, only last value for that duplicate key will be saved.
        # For example:
        #     {"a": 1, "a": 2, "b": 3} becomes {"a": 2, "b": 3}
        self.dbt_commands = Variable.get(
            "dbt_kube_dag_dbt_commands", deserialize_json=True
        )

    @staticmethod
    def sequential_append(to_task, from_task_list):
        """Append given list of tasks to a task sequentially.
        
        Args:
            to_task: A airflow.models.BaseOperator to attach our tasks to.
            from_task_list: A list of BaseOperators
        
        Given task_list = [task_2, task_3, task_4],
        
        sequential_append(
            to_task=task_1, from_task_list=task_list
        )
        
        is equivalent to
            
        task_1 >> task_2 >> task_3 >> task_4
        """
        # make a deep copy of task_list
        task_list = from_task_list[:]

        # insert task to the very front of the task_list
        task_list[:0] = [to_task]  # slicing performs better than insert(0, value)

        # set relationships sequentially
        chain(*task_list)

    def dbt_dynamic_tasks(self):
        """Create DBT tasks with commands based on config json file. Example: <name of config file you created>
        Transforms any DBT commands set in the config file into airflow tasks.
        Expected Input Format:
            dbt_commands: { task_id: dbt_command }
        Example Config:
            "dbt_commands": {
                "dbt-test_status": "dbt test --models source:status.table_name",
                "dbt-source-freshness": "dbt source snapshot-freshness --select status.table_name",
                "dbt-run": "dbt run --models model_source.table_name",
                "dbt-test-transformed": "dbt test --models model_source.table_name"
            }
        #TODO: update to be accurate
        Expected Output:
            list(
                KubernetesPodOperator(task_id: "dbt-debug", command: "dbt debug",...),
                KubernetesPodOperator(task_id: "dbt-test-status", command: "dbt test --models source:status.table_name",...),
                KubernetesPodOperator(task_id: "dbt-source-freshness", command: "dbt source snapshot-freshness --select status.table_name",...),
                KubernetesPodOperator(task_id: "dbt-run", command: "dbt run --models model_source.table_name",...),
                KubernetesPodOperator(task_id: "dbt-test-transformed", command: "dbt test --models model_source.table_name",...)
            )
        """
        # commands to pass to dbt task list
        git_clone_cmds = f"""
            git clone https://github.com/sungchun12/dbt_bigquery_example.git &&
            cd dbt_bigquery_example"""

        setup_commands_to_run = f"""
            /entrypoint.sh &&
            ls -ltr &&
            echo $DBT_DATABASE &&
            {git_clone_cmds} &&
            export DBT_PROFILES_DIR=$(pwd) &&
            export DBT_GOOGLE_BIGQUERY_KEYFILE=/dbt/account.json"""

        # ensure this is run every time regardless of config
        dbt_debug_command = {"dbt-debug": "dbt debug --target service_account_runs"}
        # consolidated dbt commands dict
        dbt_commands_to_run = {**dbt_debug_command, **self.dbt_commands}
        # call on secrets dynamically created in kubernetes cluster hosting cloud composer
        service_account = Secret(
            # Expose the secret as environment variable.
            deploy_type="env",
            # The name of the environment variable, since deploy_type is `env` rather
            # than `volume`.
            deploy_target="SERVICE_ACCOUNT",
            # Name of the Kubernetes Secret
            secret="dbt-secret",
            # Key of a secret stored in this Secret object
            key="account.json",
        )
        # standard dict in Python 3.7 preserves insertion order
        # TODO: may require in_cluster=False and providing a custom config file for local runs to work
        dbt_task_list = [
            KubernetesPodOperator(
                task_id=task_id,
                name=task_id,
                namespace="default",
                image=self.runtime_parameters.get("image"),
                cmds=["/bin/bash", "-cx"],
                arguments=[
                    f"""
                    {setup_commands_to_run} &&
                    {dbt_command}"""
                ],
                secrets=[service_account],
                # Storing sensitive credentials in env_vars will be exposed in plain text
                env_vars={"DBT_DATABASE": self.runtime_parameters.get("dbt_project")},
                image_pull_policy="Always",
                is_delete_operator_pod=True,
                get_logs=True,
                config_file=config_file,
                in_cluster=in_cluster
            )
            for task_id, dbt_command in dbt_commands_to_run.items()
        ]
        return dbt_task_list


dynamic_task_generator = dynamic_task_generator_utility()
default_args = dynamic_task_generator.default_args

with DAG("dbt_kube_dag_cloud_composer", default_args=default_args, schedule_interval=None) as dag:
    dummy_task_1 = DummyOperator(task_id="dbt_dummy_task_1")

    dbt_dynamic_tasks = dynamic_task_generator.dbt_dynamic_tasks()

dummy_task_1

dynamic_task_generator.sequential_append(
    to_task=dummy_task_1, from_task_list=dbt_dynamic_tasks
)
