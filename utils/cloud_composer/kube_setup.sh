#!/bin/bash


### Access Specific Kubernetes Container from Cloud Shell
sudo apt-get install kubectl git

gcloud composer environments run dev-composer \
    --project my-data-pipeline \
    --location us-central1 \
    list_dags

gcloud composer environments describe dev-composer \
    --location us-central1 \
    --format="value(config.gkeCluster)"

gcloud container clusters get-credentials projects/my-data-pipeline/zones/us-central1-b/clusters/us-central1-dev-composer-de094856-gke \
    --zone us-central1-b \
    --project my-data-pipeline

# copy and paste contents of service account json file from local machine into the bastion host
cat <<EOF > service_account.json
<service account file contents>
EOF

# be very careful with naming convention for this secret or else the KubernetesPodOperator will timeout
kubectl create secret generic dbt-secret --from-file=account.json

# Create SSH key pair for secure git clones
ssh-keygen

# copy and paste contents to your git repo SSH keys section
# https://github.com/settings/keys
cat ~/.ssh/id_rsa.pub

# create the ssh key secret
kubectl create secret generic ssh-key-secret --from-file=id_rsa=$HOME/.ssh/id_rsa --from-file=id_rsa.pub=$HOME/.ssh/id_rsa.pub

kubectl get secrets

kubectl get pods --all-namespaces

kubectl -n composer-1-11-2-airflow-1-10-9-de094856 \
exec -it airflow-worker-6f595f8779-8lbmv -c airflow-worker -- /bin/bash