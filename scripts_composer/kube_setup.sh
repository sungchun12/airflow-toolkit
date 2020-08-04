#!/bin/bash


### Access Specific Kubernetes Container from Cloud Shell
sudo apt-get install kubectl

gcloud composer environments run dev-composer \
    --project wam-bam-258119 \
    --location us-central1 \
    list_dags

gcloud composer environments describe dev-composer \
    --location us-central1 \
    --format="value(config.gkeCluster)"

gcloud container clusters get-credentials projects/wam-bam-258119/zones/us-central1-b/clusters/us-central1-dev-composer-22507e9d-gke \
    --zone us-central1-b \
    --project wam-bam-258119

kubectl create secret generic service-account --from-file=service_account.json

kubectl get secrets

kubectl get pods --all-namespaces

kubectl -n composer-1-11-0-airflow-1-10-9-22507e9d \
exec -it airflow-worker-67fcdf4d7c-28nnl -c airflow-worker -- /bin/bash