#!/bin/bash
#
# Script to teardown Kubernetes cluster on Docker Desktop for Mac Context

echo "***********************"
echo "Delete Kuberenetes Cluster Helm Deployment and Secrets"
echo "***********************"
# delete helm deployment
helm delete airflow

# remove anything running on port 8080 and 8001 for lingering airflow webserver deployment
lsof -i:8080 -i:8001 -Fp | sed 's/^p//' | xargs kill -9

# delete secrets for smoother setup if someone needs to change the service account
kubectl delete secret dbt-secret
kubectl delete secret gcr-key
kubectl delete secret ssh-key-secret
kubectl delete namespace airflow