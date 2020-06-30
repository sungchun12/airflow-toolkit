#!/bin/bash
#
# Script to teardown Kubernetes cluster on Docker Desktop for Mac Context

echo "***********************"
echo "Delete Kuberenetes Cluster Helm Deployment"
echo "***********************"
# delete helm deployment
helm delete airflow

# remove anything running on port 8080 for lingering airflow webserver deployment
lsof -i:8080 -Fp | sed 's/^p//' | xargs kill -9