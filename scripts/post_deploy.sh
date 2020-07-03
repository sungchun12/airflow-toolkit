#!/bin/bash
#
# source /opt/airflow/dag_environment_configs/post_deploy.sh

ls
airflow variables --import /opt/airflow/dag_environment_configs/dev/reset_dag_configs_dev_pytest.json
airflow variables --import /opt/airflow/dag_environment_configs/dev/dbt_kube_config_pytest_dev.json