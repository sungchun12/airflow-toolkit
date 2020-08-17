# airflow-toolkit

TODO: add a airflow logo with toolkit emoji, add breeze streaks

## Motivations

## Use Cases

**In Scope**

- Works on local computer with docker desktop installed
- Run meaningful example DAGs with passing unit and integration tests
- Easily setup and teardown any environment
- Sync DAGs real-time with local git repo directory
- Reusable in another kubernetes cluster
- Same DAGs work in both local desktop computer and Google Cloud Composer
- Secure cloud infrastructure and network(least privliges access and minimal public internet touchpoints)

**Out of Scope**

- Written end to end DAG tests as the dry runs are sufficient for this repo's scope
- `terratest` for terraform unit testing
- DAGs relying on external data sources outside this repo

## Table of Contents

- [Pre-requisites](##Pre-requisites)
- [Toolkit #1: Local Desktop Kubernetes Airflow Deployment](##Toolkit-#1:-Local-Desktop-Kubernetes-Airflow-Deployment)
- [Toolkit #2: Terragrunt-Driven Terraform Deployment to Google Cloud](##Toolkit-#2:-Terragrunt-Driven-Terraform-Deployment-to-Google-Cloud)
- [Toolkit #3: Simple Terraform Deployment to Google Cloud](##Toolkit-#3:-Simple-Terraform-Deployment-to-Google-Cloud)

## Pre-requisites

1. [Sign up for a free trial](https://cloud.google.com/free/?hl=ar) _OR_ use an existing GCP account
2. Manually FORK the repo through the github interface _OR_ CLONE this repo: `git clone https://github.com/sungchun12/airflow-toolkit.git`

   ![fork git repo](/docs/fork-git-repo.png)

3. Create a new Google Cloud project

   ![create gcp project](/docs/create-gcp-project.gif)

4. Get into starting position for deployment: `cd airflow-toolkit/`

## Toolkit #1: Local Desktop Kubernetes Airflow Deployment

> Note: This was ONLY tested on a Mac

### System Design

### Specific Use Cases

### How to Deploy

#### One Time Installs

[Download docker desktop](https://www.docker.com/products/docker-desktop) and start docker desktop

```bash
# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# install docker desktop
https://www.docker.com/products/docker-desktop

#enable kubernetes through docker for desktop UI

#TODO: include section about downloading kubectl and other little tools as needed

# install helm, terragrunt, terraform to local desktop
brew install helm terragrunt terraform

# Install Google Cloud SDK and follow the prompts
# https://cloud.google.com/sdk/install
curl https://sdk.cloud.google.com | bash

# close the shell and start a new one for the changes to take effect

```

- [Create a Service Account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating)
- [Enable the Service Account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#iam-service-accounts-enable-console)
- [Create a Service Account Key JSON File-should automatically download](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console)
- Move private `JSON` key into the root directory of this git repo you just cloned and rename it `account.json`(don't worry it will be officially `gitignored`)

```bash
# Authenticate with service-account key file
gcloud auth activate-service-account --key-file account.json

gcloud components install kubectl

# Configure Docker
gcloud auth configure-docker

# Create SSH key pair for secure git clones
ssh-keygen

# copy and paste contents to your git repo SSH keys section
# https://github.com/settings/keys
cat ~/.ssh/id_rsa.pub

```

After doing the above ONCE, you can run the below multiple times with the same environment result

```bash
#!/bin/bash
# follow terminal prompt after entering below command
source setup.sh

# start a remote shell in the airflow worker for ad hoc operations or to run pytests
kubectl exec -it airflow-worker-0 -- /bin/bash
```

### How to Destroy

```bash
#!/bin/bash
source teardown.sh
```

### Tradeoffs

## Toolkit #2: Terragrunt-Driven Terraform Deployment to Google Cloud

> Note: This follows the example directory structure provided by terragrunt housed within the same git repo

### System Design

### Specific Use Cases

### How to Deploy

```bash
#!/bin/bash
# assumes you are already in the the repo root directory
cd terragrunt_infrastructure_live/non-prod/us-central1/dev/

terragrunt plan-all

terragrunt validate-all

# follow terminal prompt after entering below command
terragrunt apply-all
```

### How to Destroy

```bash
#!/bin/bash
# follow terminal prompt after entering below command
terragrunt destroy-all
```

### Tradeoffs

### General Concepts

- The airflow kubernetes cluster will use the service account within the `airflow` namespace to pull the image from Google Container Registry based on the manually created secret: `gcr-key`

```bash
kubectl get serviceaccounts

NAME      SECRETS   AGE
airflow   1         43m
default   1         43m
```

- The `KubernetesPodOperator` will pull the image based on the permissions above BUT will run `dbt` operations based on the manually created secret: `dbt-secret`

```bash
kubectl get secrets

NAME                            TYPE                                  DATA   AGE
airflow-postgresql              Opaque                                1      50m
airflow-redis                   Opaque                                1      50m
airflow-token-zfpz8             kubernetes.io/service-account-token   3      50m
dbt-secret                      Opaque                                1      50m
default-token-pz55g             kubernetes.io/service-account-token   3      50m
gcr-key                         kubernetes.io/dockerconfigjson        1      50m
sh.helm.release.v1.airflow.v1   helm.sh/release.v1                    1      50m
```

### View Local Kubernetes Dashboard

```bash
# install kubernetes dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-rc3/aio/deploy/recommended.yaml

# start the web server
kubectl proxy

# view the dashboard
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy#/login

# copy and paste the token output into dashboard UI
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | awk '/^deployment-controller-token-/{print $1}') | awk '$1=="token:"{print $2}'

```

## Toolkit #3: Simple Terraform Deployment to Google Cloud

> Note: This uses terragrunt as a thin wrapper within a single subdirectory

### System Design

### Specific Use Cases

### How to Deploy

```bash
#!/bin/bash
cd terraform_simple_setup/

terragrunt plan

terragrunt validate

# follow terminal prompt after entering below command
terragrunt apply
```

### How to Destroy

```bash
#!/bin/bash
# follow terminal prompt after entering below command
terragrunt destroy
```

### Tradeoffs

## Frequently Asked Questions(FAQ)

- Why do you use identity aware proxy for remote ssh access into the bastion host?
- Do you have an equivalent deployment repo for AWS/Azure?
  - No, more than open to a pull request that includes this
- Why not use terratest?
- Why pytest?
-

## Resources

- [Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
- [Helm Chart Official Release](https://hub.helm.sh/charts/stable/airflow)
- [Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
- [SQLite issue](https://github.com/helm/charts/issues/22477)
- [kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [What is a pod?](https://kubernetes.io/docs/concepts/workloads/pods/pod/)
- [Kubernetes Dashboard for Docker Desktop](https://medium.com/backbase/kubernetes-in-local-the-easy-way-f8ef2b98be68)
- [Cost effective way to scale the airflow scheduler](https://medium.com/@royzipuff/the-smarter-way-of-scaling-with-composers-airflow-scheduler-on-gke-88619238c77b)
