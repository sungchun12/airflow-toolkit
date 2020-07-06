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
# Create SSH key pair for secure git clones
ssh-keygen

# copy and paste contents to your git repo SSH keys section
cat ~/.ssh/id_rsa.pub

```

## Setup Airflow

```bash
# optional: create a matching local venv for IDE syntax highlighting
python3 -m venv py37_venv
source py37_venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt

minikube start --cpus 4 --memory 8192

# run the full setup script
source setup.sh

# create ssh key directly into the cluster
# example:
# kubectl create secret generic ssh-key-secret --from-file=id_rsa=$HOME/.ssh/id_rsa --from-file=id_rsa.pub=$HOME/.ssh/id_rsa.pub

kubectl create secret generic ssh-key-secret --from-file=id_rsa=/path/to/.ssh/id_rsa --from-file=id_rsa.pub=/path/to/.ssh/id_rsa.pub

# start a remote shell in the airflow worker for ad hoc operations or to run pytests
kubectl exec -it airflow-worker-0 -- /bin/bash

# import variables after you're in the airflow worker remote shell
source /opt/airflow/dag_environment_configs/post_deploy.sh
airflow variables --import /opt/airflow/dag_environment_configs/dev/reset_dag_configs_dev_pytest.json
airflow variables --import /opt/airflow/dag_environment_configs/dev/dbt_kube_config_pytest_dev.json

# run pod process in background
kubectl exec -it airflow-worker-0 -- /bin/bash -c 'source /home/airflow/post_deploy/post_deploy.sh'
kubectl exec -it airflow-worker-0 -- "ls /home/airflow/post_deploy/"

find /opt/airflow/ -type d -exec chmod 775 {} \;
find /opt/airflow/ -type f -exec chmod 664 {} \;
exit

# teardown the cluster
source teardown.sh

```

## View Kubernetes Dashboard

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

## General Kubernetes Concepts

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

### Resources

- [Helm Quickstart](https://helm.sh/docs/intro/quickstart/)
- [Helm Chart Official Release](https://hub.helm.sh/charts/stable/airflow)
- [Helm Chart Source Code](https://github.com/helm/charts/tree/master/stable/airflow)
- [SQLite issue](https://github.com/helm/charts/issues/22477)
- [kubectl commands](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)
- [What is a pod?](https://kubernetes.io/docs/concepts/workloads/pods/pod/)
- [Kubernetes Dashboard for Docker Desktop](https://medium.com/backbase/kubernetes-in-local-the-easy-way-f8ef2b98be68)
