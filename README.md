# airflow-toolkit

**End Goal**: Any airflow project day 1, can spin up and get something working locally AND transferrable to a Cloud Cluster

[Airflow Helm Chart](https://hub.helm.sh/charts/stable/airflow)

**Success Criteria**:

- Works on local computer with docker desktop installed
- Run meaningful example DAGs with passing tests
- Easily setup and teardown
- Sync DAGs real-time with local git repo directory
- Can be reusable in another kubernetes cluster
- Can run pytests for component-level and end to end tests
- Same DAGs work in both local computer and Google Cloud Composer

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
#TODO: include section about downloading kubectl and other little tools as needed

# install helm
brew install helm

# Install Google Cloud SDK
# https://cloud.google.com/sdk/install
curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts

# close the shell and start a new one for the changes to take effect

# Authenticate with service-account key file
gcloud auth activate-service-account --key-file account.json

gcloud components install kubectl

# Configure Docker
gcloud auth configure-docker

```

## Setup Airflow

```bash
# run the full setup script
source setup.sh

# start a remote shell in the airflow worker for ad hoc operations or to run pytests
kubectl exec -it airflow-worker-0 -- /bin/bash

# import variables after you're in the airflow worker remote shell
airflow variables --import /opt/airflow/dag_environment_configs/dev/reset_dag_configs_dev_pytest.json
airflow variables --import /opt/airflow/dag_environment_configs/dev/dbt_kube_config_pytest_dev.json

# run pod process in background
kubectl exec -it airflow-worker-0 -- 'pytest'
kubectl exec -it airflow-worker-0 -- "ls"

# teardown the cluster
source teardown.sh

```

### Resources

[Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
[Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
[SQLite issue](https://github.com/helm/charts/issues/22477)
[kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
