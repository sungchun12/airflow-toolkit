# airflow-toolkit :rocket:

Any Airflow project day 1, you can spin up a local desktop Kubernetes Airflow environment AND a Google Cloud Composer Airflow environment with working example DAGs across both :sparkles:

TODO: add a airflow logo with toolkit emoji, add breeze streaks

## Motivations

It is a painful exercise to setup secure airflow enviroments with parity(local desktop, dev, qa, prod). Too often, I've done all this work in my local desktop airflow environment only to find out the DAGs don't work in a Kubernetes deployment or vice versa. As I got more hands-on with infrastructure/networking, it felt like I was performing two jobs: Data and DevOps engineer. Responsibilities overlap and both roles are traditionally ill-equipped to come to consensus. Either the networking specifics go over Data engineer's head and/or the data pipeline IAM permissions and DAG idempotency go over the DevOps engineer's head. There's also the issue of security and DevOps saying that spinning up an airflow-dev-cloud-environment is too risky without several development cycles to setup bastion hosts, subnets, private IPs, etc.

**This toolkit is for BOTH Data and DevOps engineers to prevent the headaches above** :astonished:

**High-Level Success Criteria:**

- Deploy airflow in 4 environments(local desktop, dev, qa, prod) in ONE day with this repo(save 4-5 weeks of development time)
- Confidence that base DAG integration components work based on successful example DAGs(save 1-2 weeks of development time)
- Simple setup and teardown for all toolkits and environments
- It FEELS less painful to iteratively develop airflow DAG code AND infrastructure as code
- Inspired to automate other painful parts of setting up airflow environments for others

## Use Cases

**In Scope**

- Works on local computer with docker desktop installed
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

## Pre-requisites

1. [Sign up for a free trial](https://cloud.google.com/free/?hl=ar) _OR_ use an existing GCP account
2. Manually FORK the repo through the github interface _OR_ CLONE this repo: `git clone https://github.com/sungchun12/airflow-toolkit.git`

   ![fork git repo](/docs/fork-git-repo.png)

3. Create a new Google Cloud project

   ![create gcp project](/docs/create-gcp-project.gif)

4. Get into starting position for deployment: `cd airflow-toolkit/`

### One Time Setup for All Toolkits

> Time to Complete: 10-20 minutes

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

* [Create a Service Account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating)

- Add the `Editor` role
  > Note: this provides wide permissions for the purposes of this demo, this will need to be updated based on your specific situation

* [Enable the Service Account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#enabling)
* [Create a Service Account Key JSON File-should automatically download](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys)
* Move private `JSON` key into the root directory of this git repo you just cloned and rename it `account.json`(don't worry it will be officially `gitignored`)

- Run the below commands in your terminal

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
# The homebrew installation above will suffice
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

## Toolkit #1: Local Desktop Kubernetes Airflow Deployment

> Note: This was ONLY tested on a Mac desktop environment

### System Design

TODO: add a full architecture diagram

### Specific Use Cases

- Free local dev environment
- Rapid DAG development without waiting for an equivalent environment to sync DAG changes
- Experiment with a wider array of customization and permissions to then handoff to DevOps
- Minimal knowledge of kubernetes and helm required

### How to Deploy

> Time to Complete: 2-3 minutes

- Run the below commands in your terminal

```bash
#!/bin/bash
# follow terminal prompt after entering below command
# leave this terminal open to sustain airflow webserver
# TODO: add setting custom env vars
source deploy_local_desktop_airflow.sh
```

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

> press `ctrl + c` within the terminal where you ran the kubernetes dashboard script to close it

## Toolkit #2: Terragrunt-Driven Terraform Deployment to Google Cloud

> Note: This follows the example directory structure provided by terragrunt with modules housed in the same git repo-[further reading](https://github.com/gruntwork-io/terragrunt-infrastructure-live-example)

### System Design

TODO: add a full architecture diagram

#### Resources

- [Keep your Terraform code DRY](https://terragrunt.gruntwork.io/docs/features/keep-your-terraform-code-dry/)
- [Relative Paths](https://community.gruntwork.io/t/relative-paths-in-terragrunt-modules/144/6)
- [Handling Dependencies](https://community.gruntwork.io/t/handling-dependencies/315/2)
- [Terraform force unlock](https://www.terraform.io/docs/commands/force-unlock.html)
- [Third Party Reasons to use terragrunt](https://transcend.io/blog/why-we-use-terragrunt)
- [Managing Terraform Secrets](https://blog.gruntwork.io/a-comprehensive-guide-to-managing-secrets-in-your-terraform-code-1d586955ace1)
- [Google Provider Documentation](https://www.terraform.io/docs/providers/google/guides/provider_reference.html#full-reference)
- [Installing Homebrew in GitHub Actions](https://github.community/t/installing-homebrew-on-linux/17994)

### Specific Use Cases

- Low cost cloud airflow dev environment($10-$20/day)
- Test local desktop DAGs against cloud infrastructure that will have more parity with qa and prod environments
- Add more horsepower to your data pipelines
- Infrastructure as code that is DevOps friendly with terraform modules that do NOT change or duplicate, only terragrunt configs change

### How to Deploy

```bash
#!/bin/bash
# assumes you are already in the the repo root directory
cd terragrunt_infrastructure_live/non-prod/us-central1/dev/

# this has mock outputs to emulate module dependencies
terragrunt plan-all

# this has mock outputs to emulate module dependencies
terragrunt validate-all

# follow terminal prompt after entering below command
# do NOT interrupt this process until finished or it will corrupt terraform state
terragrunt apply-all
```

### How to Destroy

```bash
#!/bin/bash
# follow terminal prompt after entering below command
terragrunt destroy-all
```

### Tradeoffs

## Toolkit #3: Simple Terraform Deployment to Google Cloud

> Note: This uses terragrunt as a thin wrapper within a single subdirectory

### System Design

TODO: add a full architecture diagram

### Specific Use Cases

### How to Deploy

```bash
#!/bin/bash
cd terraform_simple_setup/
# preview the cloud resources you will create
terraform plan

# validate terraform syntax and configuration
terraform validate

# follow terminal prompt after entering below command
terraform apply
```

### How to Destroy

```bash
#!/bin/bash
# follow terminal prompt after entering below command
terraform destroy
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
