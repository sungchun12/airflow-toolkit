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

# install minikube
brew install minikube

# install helm
brew install helm
```

## Setup Airflow

```bash
# start minikube
minikube start

# add helm chart repo
helm repo add stable https://kubernetes-charts.storage.googleapis.com/

# get latest list of changes
helm repo update

# install airflow helm chart
# https://helm.sh/docs/helm/helm_install/
helm install airflow stable/airflow \
    --version 7.1.5 \
    --values ./custom-values.yaml



# expected output
#####################
# NAME: airflow
# LAST DEPLOYED: Thu Jun 25 21:18:40 2020
# NAMESPACE: default
# STATUS: deployed
# REVISION: 1
# TEST SUITE: None
# NOTES:
# Congratulations. You have just deployed Apache Airflow!

# 1. Get the Airflow Service URL by running these commands:
#    export POD_NAME=$(kubectl get pods --namespace default -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")
#    echo http://127.0.0.1:8080
#    kubectl port-forward --namespace default $POD_NAME 8080:8080

# 2. Open Airflow in your web browser
#####################

# check status
helm ls

# expected output
#####################
# NAME    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
# airflow default         1               2020-06-25 21:18:40.822324 -0500 CDT    deployed        airflow-7.1.5   1.10.10
#####################

# run bash commands directly in the pod
kubectl exec \
  -it \
  --name airflow \
  --container airflow-scheduler \
  Deployment/airflow-scheduler \
  /bin/bash
```

### Resources

[Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
