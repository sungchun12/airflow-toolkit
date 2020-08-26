# #############################################################################
# Imports
# #############################################################################
import datetime
from airflow import models
from airflow.utils import dates

from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator
)

# #############################################################################
# User configurations
# #############################################################################
PROJECT = 'aaron-isolated-network'
REGION = 'us-central1'
SUBNET = 'projects/aaron-isolated-network/regions/us-central1/subnetworks/subnet3'


# #############################################################################
# Function to return the Dataproc configuration for the reusable cluster
# #############################################################################
def get_dataproc_config():
    return {
        "project_id": PROJECT,
        "cluster_name": "etl-cluster-1",
        "config": {
            "master_config": {
                "num_instances": 1,
                "machine_type_uri": "n1-standard-4",
                "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 1024},
            },
            "worker_config": {
                "num_instances": 2,
                "machine_type_uri": "n1-standard-4",
                "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 1024},
            },
            "gce_cluster_config": {
                "tags": {
                    "etl-cluster"
                },
                "metadata": {
                    "ssh-keys": "hdfs:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDAVlrNRVU4JAfExeGuMsqNUkmQFJ+aUT4lfVFhI0i73Jrvl7h2xRK4mN+FZUhxkPQ9bXKt9UdrF9wy02J+dIRbaAXcvC0MFnOZF85cyh44xf2M9Lb8JMjivNVpOiPC9fNGiTuIAWn6RX9ao45RpO+smEglsly3B9SanpmOK9yyo7cWWDOfWvW2+/3p4dD7AM8U6IvbnmEfwcQs+Qk9PJHU+BJlRJxYfKVKtGAEzeON2wZnuR3mSrrZTopF1nmXvAqAwBibTiG1U1K2e4PPoRhVVy1Kh7q2V0dC9Htt5giy0OxGZ+tPkwACrnL9/7VVbF8aggVJc64nID1UkIuNT9sNTZmQ71gSMIHd6xZ3YAj3+hG9YGAi3y8uMtCeKzjvP/rKs1WQojeWu2kcpxd3JMfSeu0mr69fYOy+hiZwGLDNPLcYhO4+mQNOeJ6vzSqbDDLMsADodJU5e/wHxYE6p9HX+IoUXfC5YzCscfY4mY0erKJ7PMR4D5CQ2e0tY+CXoZkHVtbPgfouvOikYTG9Nizj7bHEZh9hn2qKGSjQMjO43xB3joktnsWlKM5IZY+aRdLU15jDE8BFrrWjpmLRz/3X6hfUNikIRjAh687B/JFEtnqHSN3ozLOdHeL3kxvZqyT3KmHyJqs9IgdBgt9f3GyfEt/n1eJHPmnnecXv1mbMZQ== hdfs"
                },
                "subnetwork_uri": SUBNET
            }
        },
    }


# #########################################################
# ##
# ## The DAG
# ##
# #########################################################
default_dag_args = {
    'start_date': dates.days_ago(0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
    'project_id': PROJECT
}

with models.DAG(
    'Weekly-ETL-DAG-1',
    schedule_interval=None,
    start_date=datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.min.time())
) as dag:

    create_dataproc_cluster = DataprocCreateClusterOperator(
        task_id='create_dataproc_cluster',
        project_id=PROJECT,
        region=REGION,
        cluster=get_dataproc_config(),
        trigger_rule='all_done',
    )