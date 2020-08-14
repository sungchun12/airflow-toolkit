#!/usr/bin/env bash
set -e

# This script runs each time the dbt Docker image is run.
# The SERVICE_ACCOUNT variable is passed to the container
# from Cloud Composer or a VM during build. The variable
# contains the entire contents of a service account file.
# The service account file is created. The final line
# instructs the container to accept commands from a shell.

# Create account file and change permissions
echo $SERVICE_ACCOUNT > /dbt/account.json

# Accept commands passed to the container from shell.
$*