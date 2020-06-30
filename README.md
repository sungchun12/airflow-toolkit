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

# Install Google Cloud SDK
# https://cloud.google.com/sdk/install
curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts

# Authenticate with service-account key file
gcloud beta auth activate-service-account --key-file account.json

# Configure Docker
gcloud auth configure-docker

```

## Setup Airflow

```bash
# run the full setup script
source setup.sh

# start a remote shell in the airflow worker for ad hoc operations or to run pytests
kubectl exec -it airflow-worker-0 -- /bin/bash

# teardown the cluster
source teardown.sh

```

### Resources

[Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
[Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
[SQLite issue](https://github.com/helm/charts/issues/22477)
[kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
