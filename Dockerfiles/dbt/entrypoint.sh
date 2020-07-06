#!/usr/bin/env bash

# This script runs each time the dbt Docker image is run.
# The SERVICE_ACCOUNT variable is passed to the container
# from Cloud Composer or a VM during build. The variable
# contains the entire contents of a service account file.
# The service account file is created. The final line
# instructs the container to accept commands from a shell.

# Create account file and change permissions
# ssh-keyscan github.com >> /dbt/.ssh/known_hosts
# echo $SERVICE_ACCOUNT > /dbt/account.json
# echo $GIT_SECRET_ID_RSA_PRIVATE > /dbt/id_rsa

# chmod 644 /dbt/account.json
chmod 700 /dbt/

# GIT_SSH_COMMAND='ssh -i /dbt/id_rsa -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' \
# git clone -b feature-helm-local-deploy git@github.com:sungchun12/airflow-toolkit.git

# Accept commands passed to the container from shell.
$*