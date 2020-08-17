# Cloud Composer Ad Hoc Development

## What does this do?

- Ad hoc cli commands to interact with cloud composer, respective gcs buckets, and secrets manager
- Some commands work locally vs. can only be run in a VM connected directly to the private IP cloud composer cluster
- Intended for development use

## What does this NOT do?

- Scheduled runs
- For production use
- Infrastructure and permission setup

### Set Project Variables

```bash
export PROJECT_DIR=$PWD
export GCP_PROJECT="wam-bam-258119"

# Set Composer location
gcloud config set composer/location us-central1
```

### Get Cloud Composer environment details

```bash
COMPOSER_ENVIRONMENT="dev-composer"
COMPOSER_BUCKET=$(gcloud composer environments describe ${COMPOSER_ENVIRONMENT} --format='value(config.dagGcsPrefix)' | sed 's/\/dags//g')
```

### Add files to Composer Bucket

```bash
### Copy all DAGs / configs
# Sync DAGs
gsutil -m rsync -r $PROJECT_DIR/dags $COMPOSER_BUCKET/dags

# Sync DAG Configs
gsutil -m rsync -r $PROJECT_DIR/dag_environment_configs $COMPOSER_BUCKET/dag_environment_configs


### Copy individual files
# Copy single DAG
gsutil cp $PROJECT_DIR/dags/pilot_pipeline.py $COMPOSER_BUCKET/dags/

# Copy single config
gsutil cp $PROJECT_DIR/dag_environment_configs/dag_config.dev $COMPOSER_BUCKET/dag_environment_configs/
```

### Update Airflow variables with config file and list DAGs

> Note: These commands ONLY work within the VM

```bash
# Import the config file
gcloud composer environments run $COMPOSER_ENVIRONMENT variables -- --import /home/airflow/gcsfuse/dag_environment_configs/dag_config_dev.json

# See if the variable updated
gcloud composer environments run $COMPOSER_ENVIRONMENT variables -- --get default_args

# List the DAGs
gcloud composer environments run $COMPOSER_ENVIRONMENT list_dags
```

### Running and testing DAGs / tasks

> Note: These commands ONLY work within the VM

```bash
gcloud composer environments run $COMPOSER_ENVIRONMENT run -- pilot_pipeline some_task 2020-01-01

gcloud composer environments run $COMPOSER_ENVIRONMENT test -- pilot_pipeline some_task 2020-01-01
```

## Using Secrets Manager in DAGs

### Import library and set connection

```python
from google.cloud import secretmanager

secrets = secretmanager.SecretManagerServiceClient()
```

### Get the secret

```python
# Get Project ID from Airflow Variables
PROJECT_ID = Variable.get("gcp_project") # Variable refers to airflow.models.Variable module

# Get secret from Secret Manager
TEST_SECRET = secrets.access_secret_version(f"projects/{PROJECT_ID}/secrets/TEST_SECRET/versions/latest").payload.data.decode("utf-8")
```

## Updating Cloud Composer Environment

**_NOTE: These commands update the entire Composer environment and will leave Airflow in an UPDATING state for several minutes to an hour. Jenkins pipelines and other automation should also avoid calling these operations._**
[Updating Composer](https://cloud.google.com/sdk/gcloud/reference/beta/composer/environments/update)
