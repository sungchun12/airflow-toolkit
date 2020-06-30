#!/bin/bash

# Build DBT image
# Building might fail outside VM due to network security
# dbt deps command pull dbt_utils from public docker hub
# TODO: make this similar to gitlab in git cloning in real time
# https://gitlab.com/gitlab-data/analytics/-/blob/master/dags/transformation/dbt_poc.py#L47
# https://gitlab.com/gitlab-data/analytics/-/blob/master/dags/airflow_utils.py
docker build -t dbt_docker ./Dockerfiles/dbt/

# Tag
docker tag dbt_docker $DOCKER_DBT_IMG
docker tag dbt_docker latest

# Push to GCR
docker push $DOCKER_DBT_IMG