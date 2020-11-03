# dbt models for `jaffle_shop`

![dbt operations](https://github.com/sungchun12/dbt_bigquery_example/workflows/dbt%20operations/badge.svg) ![Cloud Run Website](https://github.com/sungchun12/dbt_bigquery_example/workflows/Cloud%20Run%20Website/badge.svg)

`jaffle_shop` is a fictional ecommerce store. This dbt project transforms raw
data from an app database into a customers and orders model ready for analytics.

The raw data from the app consists of customers, orders, and payments, with the
following entity-relationship diagram:

![Jaffle Shop ERD](/etc/jaffle_shop_erd.png)

This [dbt](https://www.getdbt.com/) project has a split personality:

- **Tutorial**: The [tutorial](https://github.com/fishtown-analytics/jaffle_shop/tree/master)
  branch is a useful minimum viable dbt project to get new dbt users up and
  running with their first dbt project. It includes [seed](https://docs.getdbt.com/docs/building-a-dbt-project/seeds)
  files with generated data so a user can run this project on their own warehouse.
- **Demo**: The [demo](https://github.com/fishtown-analytics/jaffle_shop/tree/demo/master)
  branch is used to illustrate how we (Fishtown Analytics) would structure a dbt
  project. The project assumes that your raw data is already in your warehouse,
  so therefore the repo cannot be run as a standalone project. The demo is more
  complex than the tutorial as it is structured in a way that can be extended for
  larger projects.

### Using this project as a tutorial

> Note: Likely use [DockerOperator or KubernetesPodOperator](https://gitlab.com/gitlab-data/analytics/-/blob/master/dags/transformation/dbt_poc.py#L47) for production deployments

To get up and running with this project

1. Clone this repository. If you need extra help, see [these instructions](https://docs.getdbt.com/docs/use-an-existing-project).

```bash
git clone https://github.com/sungchun12/dbt_bigquery_example.git
```

2. Install dbt using the below or [these instructions](https://docs.getdbt.com/docs/installation)

```bash
# change into directory
cd dbt_bigquery_example/

# setup python virtual environment locally
python3 -m venv py37_venv
source py37_venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Set up a [profile](profiles.yml) called `jaffle_shop` to connect to a data warehouse by
   following [these instructions](https://docs.getdbt.com/docs/running-a-dbt-project/using-the-command-line-interface/configure-your-profile/).
   If you have access to a data warehouse, you can use those credentials – we
   recommend setting your [target schema](https://docs.getdbt.com/docs/running-a-dbt-project/using-the-command-line-interface/configure-your-profile/#populating-your-profile)
   to be a new schema (dbt will create the schema for you, as long as you have
   the right priviliges). If you don't have access to an existing data warehouse,
   you can also setup a local postgres database and connect to it in your profile.

4. Ensure your profile is setup correctly from the command line

```bash
# set the profiles directory in an environment variable, so debug points to the right files
# set DBT_PROFILES_DIR=C:\Users\sungwon.chung\Desktop\repos\dbt_bigquery_example # for windows
# replace the below with your own repo directory
export DBT_PROFILES_DIR=$(pwd)

# setup a Google Cloud Project ID
export PROJECT_ID="your-project-id"
export PROJECT_ID="big-dreams-please"

# connect to GCP
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly

# check if the dbt files and connection work using oauth as the default
dbt debug
```

5. Load the CSVs with the demo data set. This materializes the CSVs as tables in
   your target schema. Note that a typical dbt project **does not require this
   step** since dbt assumes your raw data is already in your warehouse.

> Note: You'll likely use [sources](https://docs.getdbt.com/docs/using-sources#section-defining-sources) in your [`sources.yml`](/models/sources/sources.yml) files because dbt assumes data is already loaded into your warehouse

```bash
# see a full breakdown of how dbt is creating tables in bigquery based on the csv files in the data directory
dbt seed --show
```

6. Run the models

> Note: Based on files in this directory: [models](/models)

```bash
# creates tables/views based off the sql and yml files
dbt run

# example CLI commands for how to utilize tagged models
# https://docs.getdbt.com/docs/tags#section-selecting-models-with-tags
# Run all models tagged "staging"
dbt run --model tag:staging

# Run all models tagged "staging", except those that are tagged hourly
# should give a warning that nothing will run
dbt run --model tag:staging --exclude tag:hourly

# Run all of the models downstream of a source
dbt run --model source:dbt_bq_example+

# Run all of the models downstream of a specific source table
# nothing will happen because the DAGs are dependent on other upstream tables
dbt run --model source:dbt_bq_example.raw_orders+
```

> **NOTE:** If this steps fails, it might be that you need to make small changes to the SQL in the models folder to adjust for the flavor of SQL of your target database. Definitely consider this if you are using a community-contributed adapter.

7. Test the output of the models

> Note: runs through all the tests defined in these specific files: [models/core/schema.yml](/models/core/schema.yml), [models/staging/schema.yml](/models/staging/schema.yml)

> Note: follow this [git guide](https://github.com/fishtown-analytics/corp/blob/master/git-guide.md) for merge requests

```bash
# runs through all the tests defined in the above file by
# generating SQL for out of the box functionality such as not_null and unique fields
dbt test

# run specific types of tests
dbt test --schema
dbt test --data

# test freshness of source data
dbt source snapshot-freshness

# Snapshot freshness for all dataset tables:
dbt source snapshot-freshness --select dbt_bq_example
```

8. Generate documentation for the project

```bash
# sets up the files based on logs from the above run to eventually serve in a static website
dbt docs generate
```

9. View the documentation for the project

```bash
# launches an easy-to-use static website to navigate data lineage and understand table structures
dbt docs serve
```

10. Deploy documentation as a public website on GCP Cloud Run
    > Note: `dbt docs generate` must be run before the below can be deployed

```bash
# enable cloud run api on Google Cloud
gcloud services enable run.googleapis.com

# build the docker image locally and tag it to eventually push to container registry
# does not take into account gitignore constraints given it's built locally
# ex: docker build . --tag gcr.io/wam-bam-258119/dbt-docs-cloud-run
export PROJECT_ID="wam-bam-258119"
export IMAGE="dbt-docs-cloud-run"
export REGION="us-central1"

docker build . --tag gcr.io/$PROJECT_ID/$IMAGE

# configure gcloud CLI to push to container registry
gcloud auth configure-docker

# push locally built image to container registry
# ex: docker push gcr.io/wam-bam-258119/dbt-docs-cloud-run
docker push gcr.io/$PROJECT_ID/$IMAGE

# deploy docker image to cloud run as a public website
# ex:
# gcloud beta run deploy dbt-docs-cloud-run \
# --image gcr.io/wam-bam-258119/dbt-docs-cloud-run \
# --region us-central1 \
# --platform managed \
# --allow-unauthenticated
gcloud beta run deploy $IMAGE \
  --image gcr.io/$PROJECT_ID/$IMAGE \
  --project $PROJECT_ID \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

# you can also run the dbt static website from a local docker container after pulling it from the google container registry
docker pull gcr.io/$PROJECT_ID/$IMAGE

# run the container locally
# you can also run it in the background by adding the `--detach` flag
# ex: docker container run --publish 8080:8080 --detach gcr.io/$PROJECT_ID/$IMAGE
docker container run --publish 8080:8080 gcr.io/$PROJECT_ID/$IMAGE

# open the website in your local browser
http://localhost:8080/
```

11. Incremental updates to existing tables: [click here](https://docs.getdbt.com/docs/configuring-incremental-models#section-what-if-the-columns-of-my-incremental-model-change-)

```sql
-- Incremental models are built as tables in your data warehouse – the first time a model is run, the table is built by transforming all rows of source data. On subsequent runs, dbt transforms only the rows in your source data that you tell dbt to filter for, inserting them into the table that has already been built (the target table)

-- Typical scenario: get new, daily raw data into source table with billions of rows, then the incremental dbt model will filter for the new data in that raw source table and transform it into the target table

-- models/stg_events.sql example
-- expected output: the stg_events existing table will have updated, transformed data from raw_app_data.events
{{
    config(
        materialized='incremental'
    )
}}

select
    *,
    my_slow_function(my_column)

from raw_app_data.events

{% if is_incremental() %}

  -- this filter will only be applied on an incremental run
  where event_time > (select max(event_time) from {{ this }})

{% endif %}
```

> Note: [dbt style guide](https://github.com/fishtown-analytics/corp/blob/master/dbt_coding_conventions.md)

## GitHub Actions Workflows

- Automates testing basic functionality and leaves an audit trail that this git repo contains working code
- Triggers on push and pull request to master
- You'll have to add the proper IAM permissions for more fine-grained, enabled GCP services(not required for this demo)
- Before you run the workflows, setup below is required

1. [Create and download a service account key json file](https://cloud.google.com/docs/authentication/getting-started#command-line): Assumes you have project owner permissions
2. Add a [github secret](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets#creating-encrypted-secrets-for-a-repository) named: `DBT_GOOGLE_BIGQUERY_KEYFILE`
3. Update `TODOs` in files, especially for `PROJECT_ID`

| Name                                                         | Purpose                                                                    | Notes               | References                                                                                            |
| ------------------------------------------------------------ | -------------------------------------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------- |
| [`dbt_operations.yml`](.github/workflows/dbt_operations.yml) | Runs a majority of dbt commands in the above tutorial                      | See `TODOs` in file | [Link](https://gist.github.com/troyharvey/d61ebe704395c925bf9448183e99af3e)                           |
| [`cloud_run.yml`](.github/workflows/cloud_run.yml)           | Deploys dbt docs static website similar to what's included in the repo URL | See `TODOs` in file | [Link](https://github.com/GoogleCloudPlatform/github-actions/tree/master/example-workflows/cloud-run) |

### What is a jaffle?

A jaffle is a toasted sandwich with crimped, sealed edges. Invented in Bondi in 1949, the humble jaffle is an Australian classic. The sealed edges allow jaffle-eaters to enjoy liquid fillings inside the sandwich, which reach temperatures close to the core of the earth during cooking. Often consumed at home after a night out, the most classic filling is tinned spaghetti, while my personal favourite is leftover beef stew with melted cheese.

---

For more information on dbt:

- Read the [introduction to dbt](https://dbt.readme.io/docs/introduction).
- Read the [dbt viewpoint](https://dbt.readme.io/docs/viewpoint).
- Join the [chat](http://slack.getdbt.com/) on Slack for live questions and support.

---
