""" This file contains common operators/functions to be used across multiple DAGs """
import os
from airflow import configuration as conf
from google.cloud import secretmanager

GIT_REPO = "git@github.com:sungchun12/airflow-toolkit.git"
PROJECT_ID = "wam-bam-258119"
DBT_IMAGE = f"gcr.io/{PROJECT_ID}/dbt_docker:dev-sungwon.chung-latest"

# TODO: fix kubernetes namespace context
# namespace = conf.get("kubernetes", "NAMESPACE")
# namespace = "airflow"
namespace = "default"

env = os.environ.copy()
DEPLOYMENT_SETUP = env["DEPLOYMENT_SETUP"]
# GIT_BRANCH = env["GIT_BRANCH"]
GIT_BRANCH = "feature-work"


def get_secret(project_name, secret_name):
    """
        Returns the value of a secret in Secret Manager for use in DAGs
    """
    secrets = secretmanager.SecretManagerServiceClient()
    secret_value = (
        secrets.access_secret_version(
            "projects/" + project_name + "/secrets/" + secret_name + "/versions/latest"
        )
        .payload.data.decode("utf-8")
        .replace("\n", "")
    )
    return secret_value


# GitLab default settings for all DAGs
# https://cloud.google.com/composer/docs/how-to/using/using-kubernetes-pod-operator#gcloud
def set_kube_pod_defaults(deployment_setup):
    if deployment_setup == "local_desktop":
        kube_pod_defaults = dict(
            get_logs=True,
            image_pull_policy="Always",
            in_cluster=True,
            is_delete_operator_pod=True,
            namespace="airflow",
            cmds=["/bin/bash", "-cx"],
            config_file="/home/airflow/.kube/config",
        )
    else:  # default to cloud composer defaults
        kube_pod_defaults = dict(
            get_logs=True,
            image_pull_policy="Always",
            in_cluster=False,
            is_delete_operator_pod=True,
            namespace="default",
            cmds=["/bin/bash", "-cx"],
            # config_file="/home/airflow/composer_kube_config",
        )
    return kube_pod_defaults


def set_google_app_credentials(deployment_setup):
    if deployment_setup == "local_desktop":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/account.json"
        print(
            f"Set custom environment variable GOOGLE_APPLICATION_CREDENTIALS for deployment setup: {deployment_setup}"
        )
    else:  # default to cloud composer defaults
        print("Using existing default environment variable GOOGLE_APPLICATION_CREDENTIALS")


set_google_app_credentials(DEPLOYMENT_SETUP)
kube_pod_defaults = set_kube_pod_defaults(DEPLOYMENT_SETUP)
pod_env_vars = {"PROJECT_ID": PROJECT_ID}


# This assumes the ssh private key for the git repo will exist within the working directory of the docker container
git_clone_cmds = f"""
    GIT_SSH_COMMAND='ssh -i .ssh/id_rsa -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' git clone -b {GIT_BRANCH} {GIT_REPO}"""

# entrypoint is called specifically in these commands for smoother dynamic permissions when working with the account.json file
dbt_setup_cmds = f"""
    {git_clone_cmds} &&
    cd airflow-toolkit/dbt_bigquery_example &&
    /entrypoint.sh &&
    export DBT_PROFILES_DIR=$(pwd) &&
    export DBT_GOOGLE_BIGQUERY_KEYFILE=/dbt/account.json"""
