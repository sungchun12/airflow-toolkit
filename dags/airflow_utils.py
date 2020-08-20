""" This file contains common operators/functions to be used across multiple DAGs """
import os
from airflow import configuration as conf
from google.cloud import secretmanager

GIT_REPO = "git@github.com:sungchun12/airflow-toolkit.git"
PROJECT_ID = "wam-bam-258119"
DBT_IMAGE = f"gcr.io/{PROJECT_ID}/dbt_docker:dev-latest"

# TODO: fix kubernetes namespace context
# namespace = conf.get("kubernetes", "NAMESPACE")
# namespace = "airflow"
namespace = "default"

env = os.environ.copy()
DEPLOYMENT_SETUP = env["DEPLOYMENT_SETUP"]
# GIT_BRANCH = env["GIT_BRANCH"]
GIT_BRANCH = "feature-docs"


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

# entrypoint is called specifically in these commands for smoother dynamic permissions when working with the account.json file
# utilizes cloud source mirror repo to prevent the private IP cloud composer cluster from reaching out to the public internet for the git repo
# this also prevents an extra need to create a Cloud NAT Gateway
git_clone_cmds = f"""
    /entrypoint.sh &&
    gcloud auth activate-service-account --key-file=account.json &&
    gcloud source repos clone github_sungchun12_airflow-toolkit --project={PROJECT_ID}"""

dbt_setup_cmds = f"""
    {git_clone_cmds} &&
    cd github_sungchun12_airflow-toolkit/dbt_bigquery_example &&
    export DBT_PROFILES_DIR=$(pwd) &&
    export DBT_GOOGLE_BIGQUERY_KEYFILE=/dbt/account.json"""
