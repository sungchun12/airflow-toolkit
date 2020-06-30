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

# using bitnami chart

# install airflow helm chart
# https://helm.sh/docs/helm/helm_install/
helm install airflow stable/airflow \
    --version 7.1.6 \
    --namespace "airflow" \
    --values ./custom-setup.yaml # this will override all the values in the default values yaml and cause errors, these are just example placeholders to copy and paste into the larger file

# check pods status and deployments
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

# delete helm deployment
helm delete airflow

```

### Resources

[Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
[Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
[SQLite issue](https://github.com/helm/charts/issues/22477)
[kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
