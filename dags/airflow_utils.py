""" This file contains common operators/functions to be used across multiple DAGs """
from airflow import configuration as conf

GIT_REPO = "https://github.com/sungchun12/dbt_bigquery_example.git"
PROJECT_ID = "wam-bam-258119"
DBT_IMAGE = f"gcr.io/{PROJECT_ID}/dbt_docker:latest"

# TODO: fix kubernetes namespace context
# namespace = conf.get("kubernetes", "NAMESPACE")
namespace = "airflow"

# GitLab default settings for all DAGs
def set_kube_pod_defaults(namespace):
    if namespace == "airflow":
        kube_pod_defaults = dict(
            get_logs=True,
            image_pull_policy="Always",
            in_cluster=True,
            is_delete_operator_pod=True,
            namespace=namespace,
            cmds=["/bin/bash", "-cx"],
            config_file="/home/airflow/.kube/config",
        )
    else:
        kube_pod_defaults = dict(
            get_logs=True,
            image_pull_policy="Always",
            in_cluster=True,
            is_delete_operator_pod=True,
            namespace="default",
            cmds=["/bin/bash", "-cx"],
            config_file=None,
        )
    return kube_pod_defaults


kube_pod_defaults = set_kube_pod_defaults(namespace)
pod_env_vars = {"PROJECT_ID": PROJECT_ID}

# commands to pass to dbt task list
git_clone_cmds = f"""
    git clone {GIT_REPO}"""

dbt_setup_cmds = f"""
    {git_clone_cmds} &&
    cd dbt_bigquery_example &&
    /entrypoint.sh &&
    ls -ltr &&
    echo $PROJECT_ID &&
    export DBT_PROFILES_DIR=$(pwd) &&
    export DBT_GOOGLE_BIGQUERY_KEYFILE=/dbt/account.json"""
