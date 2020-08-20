# airflow-toolkit :rocket:

![Terragrunt Deployment-Validate Syntax and Plan](https://github.com/sungchun12/airflow-toolkit/workflows/Terragrunt%20Deployment-Validate%20Syntax%20and%20Plan/badge.svg)

Any Airflow project day 1, you can spin up a local desktop Kubernetes Airflow environment AND a Google Cloud Composer Airflow environment with working example DAGs across both :sparkles:

TODO: add a airflow logo with toolkit emoji, add breeze streaks

## Motivations

It is a painful exercise to setup secure airflow enviroments with parity(local desktop, dev, qa, prod). Too often, I've done all this work in my local desktop airflow environment only to find out the DAGs don't work in a Kubernetes deployment or vice versa. As I got more hands-on with infrastructure/networking, I was performing two jobs: Data and DevOps engineer. Responsibilities overlap and both roles are traditionally ill-equipped to come to consensus. Either the networking specifics go over the Data engineer's head and/or the data pipeline IAM permissions and DAG idempotency go over the DevOps engineer's head. There's also the issue of security and DevOps saying that spinning up an airflow-dev-cloud-environment is too risky without several development cycles to setup bastion hosts, subnets, private IPs, etc. These conversations alone can lead to several-weeks delays before you can even START DRAFTING airflow pipelines! It doesn't have to be this way.

**This toolkit is for BOTH Data and DevOps engineers to solve the problems above** :astonished:

**High-Level Success Criteria:**

- Deploy airflow in 4 environments(local desktop, dev, qa, prod) in ONE day with this repo(save 4-5 weeks of development time)
- Confidence that base DAG integration components work based on successful example DAGs(save 1-2 weeks of development time)
- Simple setup and teardown for all toolkits and environments
- It FEELS less painful to iteratively develop airflow DAG code AND infrastructure as code
- Secure and private environments by default
- You are inspired to automate other painful parts of setting up airflow environments for others

## Use Cases

**In Scope**

- Airflow works on local computer with docker desktop installed
- Run meaningful example DAGs with passing unit and integration tests
- Easily setup and teardown any environment
- Sync DAGs real-time with local git repo directory(local desktop)
- Reusable configs in another kubernetes cluster
- Same DAGs work in both local desktop computer and Google Cloud Composer
- Secure cloud infrastructure and network(least privliges access and minimal public internet touchpoints)
- Low cost/Free(assumes you have Google Cloud free-trial credits)

**Out of Scope**

- Written end to end DAG tests as the dry runs are sufficient for this repo's scope
- `terratest` for terraform unit testing
- DAGs relying on external data sources outside this repo

## Table of Contents

- [Pre-requisites](##Pre-requisites)
- [Toolkit #1: Local Desktop Kubernetes Airflow Deployment](##Toolkit-#1:-Local-Desktop-Kubernetes-Airflow-Deployment)
- [Toolkit #2: Terragrunt-Driven Terraform Deployment to Google Cloud](##Toolkit-#2:-Terragrunt-Driven-Terraform-Deployment-to-Google-Cloud)
- [Toolkit #3: Simple Terraform Deployment to Google Cloud](##Toolkit-#3:-Simple-Terraform-Deployment-to-Google-Cloud)

---

---

## Prerequisites

> Time to Complete: 5-10 minutes

1. [Sign up for a free trial](https://cloud.google.com/free/?hl=ar) _OR_ use an existing GCP account
2. Manually FORK the repo through the github interface _OR_ CLONE this repo: `git clone https://github.com/sungchun12/airflow-toolkit.git`

   ![fork git repo](/docs/fork-git-repo.png)

3. Create a new Google Cloud project

   ![create gcp project](/docs/create-gcp-project.gif)

4. Get into starting position for deployment: `cd airflow-toolkit/`

### One Time Setup for All Toolkits

> Time to Complete: 10-15 minutes

- [Download docker desktop](https://www.docker.com/products/docker-desktop) and start docker desktop

- Customize Docker Desktop for the below settings
- Click `Apply & Restart` where appropriate
  ![custom_resources](/docs/custom_resources.png)
  ![enable_kubernetes](/docs/enable_kubernetes.png)

- Run the below commands in your terminal

```bash
# install homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# install helm, terragrunt, terraform, kubectl to local desktop
brew install helm terragrunt terraform kubectl

# Install Google Cloud SDK and follow the prompts
# https://cloud.google.com/sdk/install
curl https://sdk.cloud.google.com | bash
```

- Close the current terminal and start a new one for the above changes to take effect

- [Create a Service Account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating)

- Add the `Editor` role

  > Note: this provides wide permissions for the purposes of this demo, this will need to be updated based on your specific situation

- [Enable the Service Account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#enabling)

- [Create a Service Account Key JSON File-should automatically download](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys)

- Move private `JSON` key into the root directory of this git repo you just cloned and rename it `account.json`(don't worry it will be officially `gitignored`)

- Run the below commands in your local desktop terminal

```bash
# Authenticate gcloud commands with service account key file
gcloud auth activate-service-account --key-file account.json

# Enable in scope Google Cloud APIs
gcloud services enable \
    compute.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com \
    bigquery.googleapis.com \
    storage-component.googleapis.com \
    storage.googleapis.com \
    container.googleapis.com \
    containerregistry.googleapis.com \
    composer.googleapis.com

# Store contents of private service account key in Secrets Manager to be used by airflow later within the `add_gcp_connections.py` DAG
# Create a secrets manager secret from the key
gcloud secrets create airflow-conn-secret \
    --replication-policy="automatic" \
    --data-file=account.json

# List the secret
gcloud secrets list

# verify secret contents ad hoc
gcloud secrets versions access latest --secret="airflow-conn-secret"

# Optional: install specific Google Cloud version of kubectl
# The homebrew installation earlier above will suffice
# ┌──────────────────────────────────────────────────────────────────┐
# │               These components will be installed.                │
# ├─────────────────────┬─────────────────────┬──────────────────────┤
# │         Name        │       Version       │         Size         │
# ├─────────────────────┼─────────────────────┼──────────────────────┤
# │ kubectl             │             1.15.11 │              < 1 MiB │
# │ kubectl             │             1.15.11 │             87.1 MiB │
# └─────────────────────┴─────────────────────┴──────────────────────┘
gcloud components install kubectl

# Configure Docker
gcloud auth configure-docker

# Create SSH key pair for secure git clones
ssh-keygen
```

- Copy and paste contents of command below to your git repo SSH keys section

```bash
cat ~/.ssh/id_rsa.pub
```

- [Paste public ssh key contents location](https://github.com/settings/ssh/new)

> After doing the above ONCE, you can run the below toolkits multiple times with the same results(idempotent)

---

---

## Toolkit #1: Local Desktop Kubernetes Airflow Deployment

> Time to Complete: 5-8 minutes

> Note: This was ONLY tested on a Mac desktop environment

### System Design

![local_desktop_airflow.png](/docs/local_desktop_airflow.png)

### Specific Use Cases

- Free local dev environment
- Customize local cluster resources as needed
- Rapid DAG development without waiting for an equivalent cloud environment to sync DAG changes
- Experiment with a wider array of customization and permissions
- Minimal knowledge of kubernetes and helm required

### How to Deploy

**General Mechanics**

> shell script logs will generate similar mechanics

- Set environment variables
- Build and push a custom dbt docker image
- Copy Docker for Desktop Kube Config into git repo
- Download stable helm repo
- Setup Kubernetes airflow namespace
- Create Kubernetes Secrets for the local cluster to download docker images from Google Container Registry based on Service Account
- Create Kubernetes Secrets for dbt operations based on Service Account and ssh-keygen, to be used later in KubernetesPodOperator
- Setup and Install Airflow Kubernetes Cluster with Helm
- Wait for the Kubernetes Cluster to settle
- Open airflow UI webserver from terminal

---

> Note: I plan to automate this yaml setup in a future feature

- Manually update the extraVolumes section within `custom-setup.yaml`, starting at `line 174`
- Run `pwd` in your terminal from the root `airflow-toolkit/` directory and replace all the `<YOUR GIT REPO DIRECTORY HERE>` placeholders

```yaml
extraVolumes: # this will create the volume from the directory
  - name: dags
    hostPath:
      path: <YOUR GIT REPO DIRECTORY HERE>/dags/
  - name: dag-environment-configs
    hostPath:
      path: <YOUR GIT REPO DIRECTORY HERE>/dag_environment_configs/
  - name: kube-config
    hostPath:
      path: <YOUR GIT REPO DIRECTORY HERE>/.kube/
  - name: service-account
    hostPath:
      path: <YOUR GIT REPO DIRECTORY HERE>/account.json
  - name: tests
    hostPath:
      path: <YOUR GIT REPO DIRECTORY HERE>/tests/
  - name: post-deploy
    hostPath:
      path: <YOUR GIT REPO DIRECTORY HERE>/scripts/

# example below
extraVolumes: # this will create the volume from the directory
  - name: dags
    hostPath:
      path: /Users/sung/Desktop/airflow-toolkit/dags/
  - name: dag-environment-configs
    hostPath:
      path: /Users/sung/Desktop/airflow-toolkit/dag_environment_configs/
  - name: kube-config
    hostPath:
      path: /Users/sung/Desktop/airflow-toolkit/.kube/
  - name: service-account
    hostPath:
      path: /Users/sung/Desktop/airflow-toolkit/account.json
  - name: tests
    hostPath:
      path: /Users/sung/Desktop/airflow-toolkit/tests/
  - name: post-deploy
    hostPath:
      path: /Users/sung/Desktop/airflow-toolkit/scripts/
```

- Run the below commands in your terminal

```bash
#!/bin/bash
# follow terminal prompt after entering below command
# leave this terminal open to sustain airflow webserver
# Set of environment variables
export ENV="dev"
export PROJECT_ID="wam-bam-258119"
export DOCKER_DBT_IMG="gcr.io/$PROJECT_ID/dbt_docker:${ENV}-latest"

source deploy_local_desktop_airflow.sh
```

- Turn on all the DAGs using the on/off button on the left side of the UI
- After waiting a couple minutes, all the DAGs should succeed
  > Note: `bigquery_connection_check` will fail unless `add_gcp_connections` succeeds first

![local_desktop_airflow.png](/docs/local_desktop_airflow_success.png)

> Note: the airflow webserver may freeze given resource limitations

> press `ctrl + c` within the terminal where you ran the deploy script

> Run the below commands in your terminal(these already exist within the deploy script)

```bash
# view airflow UI
export POD_NAME=$(kubectl get pods --namespace airflow -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")

echo "airflow UI webserver --> http://127.0.0.1:8080"

kubectl port-forward --namespace airflow $POD_NAME 8080:8080
```

- Open a SEPARATE terminal and run the below commands

```bash
# start a remote shell in the airflow worker for ad hoc operations or to run pytests
kubectl exec -it airflow-worker-0 -- /bin/bash
```

- Airflow worker remote shell examples

```bash
➜  airflow-toolkit git:(feature-docs) ✗ kubectl exec -it airflow-worker-0 -- /bin/bash
airflow@airflow-worker-0:/opt/airflow$ ls
airflow.cfg  dag_environment_configs  dags  logs  tests  unittests.cfg
airflow@airflow-worker-0:/opt/airflow$ pytest -vv --disable-pytest-warnings
======================================== test session starts ========================================
platform linux -- Python 3.6.10, pytest-5.4.3, py-1.9.0, pluggy-0.13.1 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /opt/airflow
plugins: celery-4.4.2
collected 19 items

tests/test_add_gcp_connections.py::test_import_dags PASSED                                    [  5%]
tests/test_add_gcp_connections.py::test_contains_tasks PASSED                                 [ 10%]
tests/test_add_gcp_connections.py::test_task_dependencies PASSED                              [ 15%]
tests/test_add_gcp_connections.py::test_schedule PASSED                                       [ 21%]
tests/test_add_gcp_connections.py::test_task_count_test_dag PASSED                            [ 26%]
tests/test_add_gcp_connections.py::test_tasks[t1] PASSED                                      [ 31%]
tests/test_add_gcp_connections.py::test_tasks[t2] PASSED                                      [ 36%]
tests/test_add_gcp_connections.py::test_end_to_end_pipeline SKIPPED                           [ 42%]
tests/test_dbt_example.py::test_import_dags PASSED                                            [ 47%]
tests/test_dbt_example.py::test_contains_tasks PASSED                                         [ 52%]
tests/test_dbt_example.py::test_task_dependencies PASSED                                      [ 57%]
tests/test_dbt_example.py::test_schedule PASSED                                               [ 63%]
tests/test_dbt_example.py::test_task_count_test_dag PASSED                                    [ 68%]
tests/test_dbt_example.py::test_dbt_tasks[dbt_debug] PASSED                                   [ 73%]
tests/test_dbt_example.py::test_dbt_tasks[dbt_run] PASSED                                     [ 78%]
tests/test_dbt_example.py::test_dbt_tasks[dbt_test] PASSED                                    [ 84%]
tests/test_dbt_example.py::test_end_to_end_pipeline SKIPPED                                   [ 89%]
tests/test_sample.py::test_answer PASSED                                                      [ 94%]
tests/test_sample.py::test_f PASSED                                                           [100%]

============================= 17 passed, 2 skipped, 1 warning in 39.77s =============================
airflow@airflow-worker-0:/opt/airflow$ airflow list_dags
[2020-08-18 19:17:09,579] {__init__.py:51} INFO - Using executor CeleryExecutor
[2020-08-18 19:17:09,580] {dagbag.py:396} INFO - Filling up the DagBag from /opt/airflow/dags
Set custom environment variable GOOGLE_APPLICATION_CREDENTIALS for deployment setup: local_desktop
Set custom environment variable GOOGLE_APPLICATION_CREDENTIALS for deployment setup: local_desktop


-------------------------------------------------------------------
DAGS
-------------------------------------------------------------------
add_gcp_connections
bigquery_connection_check
dbt_example
kubernetes_sample
tutorial
```

### How to Destroy

> Time to Complete: 1-2 minutes

```bash
#!/bin/bash
source teardown_local_desktop_airflow.sh
```

- Example terminal output

```bash
➜  airflow-toolkit git:(feature-docs) ✗ source teardown_local_desktop_airflow.sh
***********************
Delete Kuberenetes Cluster Helm Deployment and Secrets
***********************
release "airflow" uninstalled
kill: illegal process id: f19
secret "dbt-secret" deleted
secret "gcr-key" deleted
secret "ssh-key-secret" deleted
namespace "airflow" deleted
```

### How to give local desktop airflow more horsepower :horse:

- [Scaling airflow resources](https://www.astronomer.io/guides/airflow-scaling-workers/)

### Tradeoffs

#### Pros

- Simple setup and no need to worry about manually destroying airflow cloud infrastructure
- Free(minimal to no charges to your Google Cloud account)
- Same example DAGs work as is in cloud infrastructure setup
- Minimal kubernetes/helm skills required to start
- Ability to scale infrastructure locally(ex: add more worker pods)
- Run `pytest` directly within this setup

#### Cons

- Limited to how much processing power and storage you have on your local desktop machine
- Airflow webserver can freeze occasionally and requires quick restart

### General Kubernetes Concepts

- The local desktop airflow kubernetes cluster will use the service account within the `airflow` namespace to pull the image from Google Container Registry based on the manually created secret: `gcr-key`

```bash
kubectl get serviceaccounts

NAME      SECRETS   AGE
airflow   1         43m
default   1         43m
```

- The `KubernetesPodOperator` will pull the docker image based on the permissions above BUT will run `dbt` operations based on the manually created secret: `dbt-secret`

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

> Optional: Detailed resource management view for local desktop

```bash
# install kubernetes dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-rc3/aio/deploy/recommended.yaml

# start the web server
kubectl proxy

# view the dashboard
open http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy#/login

# copy and paste the token output into dashboard UI
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | awk '/^deployment-controller-token-/{print $1}') | awk '$1=="token:"{print $2}'
```

![kube_resource_dashboard](/docs/kube_resource_dashboard.png)

> Enter `ctrl + c` within the terminal where you ran the kubernetes dashboard script to close it

---

---

## Toolkit #2: Terragrunt-Driven Terraform Deployment to Google Cloud

> Time to Complete: 50-60 minutes(majority of time waiting for cloud composer to finish deploying)

> Note: This follows the example directory structure provided by terragrunt with modules housed in the same git repo-[further reading](https://github.com/gruntwork-io/terragrunt-infrastructure-live-example)

### System Design

![terragrunt_deployment](/docs/terragrunt_deployment.png)

> terraform state will be split into multiple files per module

#### Terragrunt Resources

- [Keep your Terraform code DRY](https://terragrunt.gruntwork.io/docs/features/keep-your-terraform-code-dry/)
- [Relative Paths](https://community.gruntwork.io/t/relative-paths-in-terragrunt-modules/144/6)
- [Handling Dependencies](https://community.gruntwork.io/t/handling-dependencies/315/2)
- [Terraform force unlock](https://www.terraform.io/docs/commands/force-unlock.html)
- [Third Party Reasons to use terragrunt](https://transcend.io/blog/why-we-use-terragrunt)
- [Managing Terraform Secrets](https://blog.gruntwork.io/a-comprehensive-guide-to-managing-secrets-in-your-terraform-code-1d586955ace1)
- [Google Provider Documentation](https://www.terraform.io/docs/providers/google/guides/provider_reference.html#full-reference)

### Specific Use Cases

- Low cost Google Cloud dev airflow dev environment($10-$20/day)
- Test local desktop DAGs against cloud infrastructure that will have more parity with qa and prod environments
- Add more horsepower to your data pipelines
- Infrastructure as code that is DevOps friendly with terraform modules that do NOT change or duplicate, only terragrunt configs change

### How to Deploy

> Read Post-Deployment Instructions for Toolkits #2 & #3 after this deployment

- Create a service account secret to authorize the terragrunt/terraform deployment

```bash
#!/bin/bash
# create a secrets manager secret from the key
gcloud secrets create terraform-secret \
    --replication-policy="automatic" \
    --data-file=account.json

# List the secret
# example terminal output
# NAME                 CREATED              REPLICATION_POLICY  LOCATIONS
# airflow-conn-secret  2020-08-18T19:45:50  automatic           -
# terraform-secret     2020-08-12T14:34:50  automatic           -
gcloud secrets list


# verify secret contents ad hoc
gcloud secrets versions access latest --secret="terraform-secret"
```

```bash
#!/bin/bash
# assumes you are already in the the repo root directory
cd terragrunt_infrastructure_live/non-prod/us-central1/dev/

# export the Google Cloud project ID where the secrets live-to be used by terragrunt
# example: export PROJECT_ID="wam-bam-258119"
export PROJECT_ID=<your project id>

gcloud config set project $PROJECT_ID #TODO: add this step to the CICD pipeline rather than the get secret shell script

# this has mock outputs to emulate module dependencies with a prefix "mock-"
# OR you can run a more specific plan
# terragrunt plan-all -out=terragrunt_plan
terragrunt plan-all

# this has mock outputs to emulate module dependencies
terragrunt validate-all

# follow terminal prompt after entering below command
# do NOT interrupt this process until finished or it will corrupt terraform state
# OR you can apply a more specific plan
# terragrunt apply-all terragrunt_plan
terragrunt apply-all

```

### How to Destroy

> Time to Complete: 5-10 minutes

```bash
#!/bin/bash
# follow terminal prompt after entering below command
terragrunt destroy-all
```

### Tradeoffs

#### Pros

- Explicit terraform module dependencies(through terragrunt functionality)
- Keeps your terraform code DRY
- terraform state is divided by module
- Separate config and terraform module management
- Ability to spin up multiple environments(dev, qa) with a single `terragrunt plan-all` command within the dir: `./terragrunt_infrastructure_live/non-prod/`
- Same example DAGs work as is in local desktop setup
- Minimal kubernetes skills required to start
- Access to more virtual horsepower(ex: add more worker pods through cloud composer configs)
- Dynamically authorizes infrastructure operations through secrets manager
- A DevOps engineer should only need to copy and paste the dev terragrunt configs and update inputs for other environments(qa, prod)
- VPC-native, private-IP, bastion host, ssh via identity aware proxy, and other security-based, reasonable defaults(minimal touchpoints with the public internet)

#### Cons

- You must destroy your respective dev environments every day or risk accruing costs for idle resources
- Time to complete is long
- Destroying all the infrastructure through terragrunt/terraform does NOT automatically destroy the cloud composer gcs bucket used to sync DAGs-[further reading](https://www.terraform.io/docs/providers/google/r/composer_environment.html)
- If you customize the VPC to prevent any kind of public internet access, cloud composer will not deploy properly(as it needs to reach out to pypi for python dependencies)
- Need to learn another tool: terragrunt(definitely worth it)

---

---

## Toolkit #3: Simple Terraform Deployment to Google Cloud

> Time to Complete: 50-60 minutes(majority of time waiting for cloud composer to finish deploying)

> Note: This uses terragrunt as a thin wrapper within a single subdirectory

### System Design

![terragrunt_deployment](/docs/terragrunt_deployment.png)

> terraform state will be stored in one file

### Specific Use Cases

- Best used for quick and easy setup for a data engineer, NOT intended for hand off to a DevOps engineer
- Low cost Google Cloud dev airflow dev environment($10-$20/day)
- Test local desktop DAGs against cloud infrastructure that will have more parity with qa and prod environments
- Add more horsepower to your data pipelines

### How to Deploy

> Read Post-Deployment Instructions for Toolkits #2 & #3 after this deployment

- Create a service account secret to authorize the terraform deployment

```bash
#!/bin/bash
# create a secrets manager secret from the key
gcloud secrets create terraform-secret \
    --replication-policy="automatic" \
    --data-file=account.json

# List the secret
# example terminal output
# NAME                 CREATED              REPLICATION_POLICY  LOCATIONS
# airflow-conn-secret  2020-08-18T19:45:50  automatic           -
# terraform-secret     2020-08-12T14:34:50  automatic           -
gcloud secrets list


# verify secret contents ad hoc
gcloud secrets versions access latest --secret="terraform-secret"
```

```bash
#!/bin/bash

cd terraform_simple_setup/

# preview the cloud resources you will create
# OR you can run a more specific plan
# terraform plan -out=terraform_plan
terraform plan

# validate terraform syntax and configuration
terraform validate

# follow terminal prompt after entering below command
# OR you can apply a more specific plan
# terraform apply terraform_plan
terraform apply
```

### How to Destroy

> Time to Complete: 5-10 minutes

```bash
#!/bin/bash
# follow terminal prompt after entering below command
terraform destroy
```

### Tradeoffs

#### Pros

- Explicit terraform module dependencies(through built-in terraform functionality)
- Separate config and terraform module management
- Same example DAGs work as is in local desktop setup
- Minimal kubernetes skills required to start
- Access to more virtual horsepower(ex: add more worker pods through cloud composer configs)
- Dynamically authorizes infrastructure operations through secrets manager
- A DevOps engineer should only need to copy and paste the dev terragrunt configs and update inputs for other environments(qa, prod)
- VPC-native, private-IP, bastion host, ssh via identity aware proxy, and other security-based, reasonable defaults(minimal touchpoints with the public internet)

#### Cons

- You must destroy your respective dev environments every day or risk accruing costs for idle resources
- Time to complete is long
- Destroying all the infrastructure through terragrunt/terraform does NOT automatically destroy the cloud composer gcs bucket used to sync DAGs-[further reading](https://www.terraform.io/docs/providers/google/r/composer_environment.html)
- If you customize the VPC to prevent any kind of public internet access, cloud composer will not deploy properly(as it needs to reach out to pypi for python dependencies)
- To create a similar environment(qa, prod), you would have to copy and paste the terraform modules into a separate directory and run the above steps. Terraform code is NOT DRY
- The DevOps engineer has to take on a lot more work to maintain this deployment across several environments
- terraform state is all contained within one file

---

---

## Post-Deployment Instructions for Toolkits #2 & #3

> Time to Complete: 5-10 minutes

- After the terragrunt/terraform deployment is successful, run the below commands in your local desktop terminal

```bash
#!/bin/bash

# ssh via identity aware proxy into the bastion host(which will then run commands against cloud composer)
source utils/cloud_composer/iap_ssh_tunnel.sh

# install basic software in the bastion host
sudo apt-get install kubectl git

# Set Composer project, location, and zone
# Minimizes redundant flags in downstream commands
gcloud config set project wam-bam-258119
gcloud config set composer/location us-central1
gcloud config set compute/zone us-central1-b

# list cloud composer DAGs
gcloud composer environments run dev-composer \
    list_dags

# capture cloud composer environment config
COMPOSER_ENVIRONMENT="dev-composer"
COMPOSER_CONFIG=$(gcloud composer environments describe ${COMPOSER_ENVIRONMENT} --format='value(config.gkeCluster)')
# COMPOSER_CONFIG ex: projects/wam-bam-258119/zones/us-central1-b/clusters/us-central1-dev-composer-de094856-gke

# capture kubernetes credentials and have kubectl commands point to this cluster
gcloud container clusters get-credentials $COMPOSER_CONFIG

# copy and paste contents of service account json file from local machine into the bastion host
cat <<EOF > account.json
<paste service account file contents>
EOF

# be very careful with naming convention for this secret or else the KubernetesPodOperator will timeout
kubectl create secret generic dbt-secret --from-file=account.json

# Create SSH key pair for secure git clones
ssh-keygen

# copy and paste contents to your git repo SSH keys section
# https://github.com/settings/keys
cat ~/.ssh/id_rsa.pub

# create the ssh key secret
kubectl create secret generic ssh-key-secret \
  --from-file=id_rsa=$HOME/.ssh/id_rsa \
  --from-file=id_rsa.pub=$HOME/.ssh/id_rsa.pub

kubectl get secrets
```

- Open a separate terminal to run the below

```bash
#!/bin/bash

# add secrets manager IAM policy binding to composer service account
PROJECT_ID="wam-bam-258119"
MEMBER_SERVICE_ACCOUNT_EMAIL="serviceAccount:composer-sa-dev@wam-bam-258119.iam.gserviceaccount.com" #TODO: make this dynamic
SECRET_ID="airflow-conn-secret"

gcloud secrets add-iam-policy-binding $SECRET_ID \
    --member=$MEMBER_SERVICE_ACCOUNT_EMAIL \
    --role="roles/secretmanager.secretAccessor"

# Configure variables to interact with cloud composer
export PROJECT_DIR=$PWD

# Set Composer location
gcloud config set composer/location us-central1

COMPOSER_ENVIRONMENT="dev-composer"
COMPOSER_BUCKET=$(gcloud composer environments describe ${COMPOSER_ENVIRONMENT} --format='value(config.dagGcsPrefix)' | sed 's/\/dags//g')

# sync files in dags folder to the gcs bucket linked to cloud composer
gsutil -m rsync -r $PROJECT_DIR/dags $COMPOSER_BUCKET/dags
```

- Access the airflow webserver UI #TODO: add more details about getting to the URL and how to sign-in
- Rerun all DAGs within cloud composer for success validation

---

---

## Git Repo Folder Structure

| Folder                            | Purpose                                                                                 |
| --------------------------------- | --------------------------------------------------------------------------------------- |
| .github/workflows                 | Quick terragrunt/terraform validations                                                  |
| dags                              | Jenkins draft code to build, test, and deploy code to various Google Cloud environments |
| dbt_bigquery_example              | Working and locally tested dbt code which performs BigQuery SQL transforms              |
| Dockerfiles                       | Docker images to be used by Cloud Composer                                              |
| docs                              | Images and other relevant documentation                                                 |
| terraform_simple_setup            | Terraform modules for a terraform-only setup                                            |
| terragrunt_infrastructure_live    | Terragrunt orchestrator to run terraform operations                                     |
| terragrunt_infrastructure_modules | Base terraform modules for terragrunt to consume in the `live` directory                |
| tests                             | Example DAG test cases                                                                  |
| utils                             | Various utilities to automate more specific ad hoc tasks                                |

## Frequently Asked Questions(FAQ)

- Why do you use identity aware proxy for remote ssh access into the bastion host?
- Do you have an equivalent deployment repo for AWS/Azure?
  - No, more then open to a pull request that includes this
- Why not use terratest?
- Why pytest?

## Resources

- [Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
- [Helm Chart Official Release](https://hub.helm.sh/charts/stable/airflow)
- [Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
- [SQLite issue](https://github.com/helm/charts/issues/22477)
- [kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [What is a pod?](https://kubernetes.io/docs/concepts/workloads/pods/pod/)
- [Kubernetes Dashboard for Docker Desktop](https://medium.com/backbase/kubernetes-in-local-the-easy-way-f8ef2b98be68)
- [Cost effective way to scale the airflow scheduler](https://medium.com/@royzipuff/the-smarter-way-of-scaling-with-composers-airflow-scheduler-on-gke-88619238c77b)
- [Kubernetes on Docker Desktop Limitations](https://docs.docker.com/docker-for-mac/kubernetes/)
- [Installing Homebrew in GitHub Actions](https://github.community/t/installing-homebrew-on-linux/17994)
