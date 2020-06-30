# airflow-toolkit

End Goal: Any airflow project day 1, can spin up and get something working locally AND cloud composer with simple setup

[Airflow Helm Chart](https://hub.helm.sh/charts/stable/airflow)

Success Criteria:

- Setup on any macbook pro
- Run a 2 meaningful example DAGs
- Idempotent(rerun the setup scripts as many times)
- NOT meant for CICD pipeline runs
- May have to write different configs for
- Can run pytests
- Same DAGs work in both local and GCP

## One Time Installs

[Download docker desktop](https://www.docker.com/products/docker-desktop) and start docker desktop

```bash
# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# install docker desktop
https://www.docker.com/products/docker-desktop

#enable kubernetes through docker for desktop UI

# install minikube
# brew install minikube

# install helm
brew install helm

# load kube config into local git repo
# this takes the docker desktop kube config to run pods on the host
# https://www.astronomer.io/docs/cli-kubepodoperator/#run-your-container
KUBE_CONFIG=$(cat $HOME/.kube/config)
mkdir -p ./.kube/ && echo $KUBE_CONFIG > ./.kube/config

```

## Setup Airflow

```bash
# start minikube
# minikube start

# add helm chart repo
helm repo add stable https://kubernetes-charts.storage.googleapis.com/

# get latest list of changes
helm repo update

# export PARENT_DIR="$(dirname `pwd`)"
kubectl create namespace airflow

# check if it's created
kubectl get namespaces

# swtich to airflow namespace
kubectl config set-context $(kubectl config current-context) --namespace="airflow"
kubectl config view | grep namespace
kubectl get pods

# Create docker-registry key for k3d
kubectl create secret docker-registry gcr-key --docker-server=gcr.io --docker-username=_json_key --docker-password="$(cat account.json)" --docker-email=example@example.com

# Set default k3d serviceaccount to use our created gcr-key for pulling images
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-key"}]}'

# create dbt-secret with SERVICE_ACCOUNT
kubectl create secret generic dbt-secret --from-file=account.json

# list all the secrets
kubectl get secrets

# install airflow helm chart
# https://helm.sh/docs/helm/helm_install/
helm install airflow stable/airflow \
    --version 7.1.6 \
    --namespace "airflow" \
    --values ./custom-setup.yaml

# check pods status and deployments
# wait 15 seconds
kubectl get deployments
kubectl get pods

# scale the scheduler
# kubectl scale deployments/airflow-scheduler --replicas=2

# view airflow UI
export POD_NAME=$(kubectl get pods --namespace airflow -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")

echo http://127.0.0.1:8080

kubectl port-forward --namespace airflow $POD_NAME 8080:8080

# check status
helm ls


# start a remote shell in the airflow worker
kubectl exec -it airflow-worker-0 -- /bin/bash

# upgrade helm with custom values
# helm upgrade -f custom-setup.yaml airflow ./airflow
helm upgrade airflow stable/airflow \
    --version 7.1.6 \
    --namespace "airflow" \
    --values ./custom-setup.yaml

# delete helm deployment
helm delete airflow

```

### Resources

[Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
[Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
[SQLite issue](https://github.com/helm/charts/issues/22477)
[kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
