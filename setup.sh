#!/bin/bash
#
# Script to setup Kubernetes cluster on Docker Desktop for Mac Context

echo "***********************"
echo "Persist Environment Variables"
echo "***********************"
source ./scripts/env.sh

echo "***********************"
echo "Build and push custom dbt docker image to Google Container Registry"
echo "***********************"
source ./scripts/dbt_docker.sh

echo "***********************"
echo "Copy Docker for Desktop Kube Config into git repo"
echo "***********************"
# load kube config into local git repo
# this takes the docker desktop kube config to run pods on the host
# https://www.astronomer.io/docs/cli-kubepodoperator/#run-your-container
KUBE_CONFIG=$(cat $HOME/.kube/config)
mkdir -p ./.kube/ && echo $KUBE_CONFIG > ./.kube/config

echo "***********************"
echo "Download stable helm repo"
echo "***********************"
# add helm chart repo
helm repo add stable https://kubernetes-charts.storage.googleapis.com/

# get latest list of changes
helm repo update

echo "***********************"
echo "Setup Kubernetes airflow namespace"
echo "***********************"
# export PARENT_DIR="$(dirname `pwd`)"
kubectl create namespace airflow

# check if it's created
kubectl get namespaces

# swtich to airflow namespace
kubectl config set-context $(kubectl config current-context) --namespace="airflow"
kubectl config view | grep namespace
kubectl get pods

echo "***********************"
echo "Create Kubernetes Secrets for the local cluster to download docker images from Google Container Registry based on Service Account"
echo "***********************"
# Create docker-registry key for Kubernetes
kubectl create secret docker-registry gcr-key --docker-server=gcr.io --docker-username=_json_key --docker-password="$(cat account.json)" --docker-email=example@example.com

# Set default kubernetes serviceaccount to use our created gcr-key for pulling images
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-key"}]}'

echo "***********************"
echo "Create Kubernetes Secrets for dbt operations based on Service Account, to be used later in KubernetesPodOperator"
echo "***********************"
# create dbt-secret with SERVICE_ACCOUNT
kubectl create secret generic dbt-secret --from-file=account.json

# list all the secrets
kubectl get secrets

echo "***********************"
echo "Setup and Install Airflow Kubernetes Cluster with Helm"
echo "***********************"
# install airflow helm chart
# https://helm.sh/docs/helm/helm_install/
helm install airflow stable/airflow \
--version 7.1.6 \
--namespace "airflow" \
--values ./custom-setup.yaml

echo "***********************"
echo "Wait for the Kubernetes Cluster to settle"
echo "***********************"
sleep 15s

kubectl get deployments
kubectl get pods

# check status
helm ls

# view airflow UI
export POD_NAME=$(kubectl get pods --namespace airflow -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")

echo "airflow UI webserver --> http://127.0.0.1:8080"

kubectl port-forward --namespace airflow $POD_NAME 8080:8080

