#!/bin/bash
#
# Set of environment variables
export ENV="dev"
# export SCRIPT_DIR="$(pwd)"
# export PARENT_DIR="$(dirname `pwd`)"
# export PROJECT_DIR="$(dirname "$PARENT_DIR")"

# Export service account key to the Environment Variable
#
# 1) When you have the service account key file
# export SERVICE_ACCOUNT=$(cat account.json)
#
# 2) Get service account key from local directory
export SERVICE_ACCOUNT=$(cat account.json)
export GCP_PROJECT="wam-bam-258119"

# set kubernetes config to k3d
# export KUBECONFIG="$(k3d get-kubeconfig --name='k3s-default')"

# Docker Airflow - Generic
# export DOCKER_AIRFLOW_IMG="puckel/docker-airflow"
# export DOCKER_AIRFLOW_NAME="kube-docker-airflow"

# Docker DBT
export DOCKER_DBT_IMG="gcr.io/$GCP_PROJECT/dbt_docker:${ENV}-$(whoami)-latest"
