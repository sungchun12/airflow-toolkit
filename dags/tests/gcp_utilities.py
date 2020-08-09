# -*- coding: utf-8 -*-
#!/usr/bin/env python3

from google.cloud import storage, bigquery
import os
from google.cloud.exceptions import NotFound, Conflict

# run this in a bash shell to authenticate with python
# export GOOGLE_APPLICATION_CREDENTIALS=<full path to service account file>

# TODO: (developer)-update this based on testing needs
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/account.json" Not needed on VM since credential file is pulled from metadata
# on airflow vm
# os.environ[
#     "GOOGLE_APPLICATION_CREDENTIALS"
# ] = "/home/vc_bryan_n_swegman/dbt_bigquery_example/airflow_setup/service_account.json"

# TODO: (developer)-update this to the base directory of the project. Line 15 of README in this directory
# Ex: export PROJECT_DIR=/home/znbingha/finance_metrics
PROJECT_DIR = os.environ["PROJECT_DIR"]

# TODO: (developer)-update this based on testing needs
utility_configs = {
    "project_name": "gcp-ushi-daci-npe",
    "dataset_name": "finance_metrics_staging_PYTEST",
    "dataset_location": "us-east4",
    "raw_data_bucket": "daci_npe_landing",
    "raw_data_bucket_path": "unit_test_archive/raw_data/",
    "raw_schemas_bucket_path": "unit_test_archive/schemas/",
}


# TODO: (developer)-update this based on testing needs
files_list = [
    "assortment.json",
    "business_area.json",
    "corporate.json",
    "customer_group_type.json",
    "daily_inventory.csv",
    "invoice_header_detail_combined.csv",
]


class gcp_utilities:
    """A set of general gcp utilities for bigquery and google cloud storage.
    Primarily for testing purposes.
    """

    def __init__(self, utility_configs):
        self.project_name = utility_configs["project_name"]
        # setup bigquery config
        self.dataset_name = utility_configs["dataset_name"]
        self.bigquery_client = bigquery.Client(self.project_name)
        self.dataset = self.bigquery_client.dataset(self.dataset_name)
        self.dataset_location = utility_configs["dataset_location"]

        # setup google cloud storage config
        self.storage_client = storage.Client()
        self.raw_data_bucket_name = utility_configs["raw_data_bucket"]
        self.raw_data_bucket = self.storage_client.bucket(self.raw_data_bucket_name)

        # where the raw local files are located
        # self.raw_data_path_dir = utility_configs["raw_data_path_dir"]
        # self.raw_schema_file_path_dir = utility_configs["raw_schema_file_path_dir"]

        # raw data specifics in gcs
        # self.raw_data_type = utility_configs["raw_data_type"]
        # self.raw_schema_file_type = utility_configs["raw_schema_file_type"]
        # self.file_table_names_list = utility_configs["file_table_names_list"]
        self.raw_data_bucket_path = utility_configs["raw_data_bucket_path"]
        self.raw_schemas_bucket_path = utility_configs["raw_schemas_bucket_path"]

    def upload_raw_schemas(self):
        """Uploads a file to the bucket based on the file_table_names_list."""
        for i in self.file_table_names_list:
            file_location = (
                self.raw_schema_file_path_dir + i + "_schema" + self.raw_data_type
            )
            destination_blob_name = (
                self.raw_schemas_bucket_path + i + "_schema" + self.raw_schema_file_type
            )
            # setup file to officially land
            blob = self.raw_data_bucket.blob(destination_blob_name)
            # upload the file
            blob.upload_from_filename(file_location)
            print("File {} uploaded to {}".format(file_location, destination_blob_name))

    def upload_raw_data(self):
        """Uploads a file to the bucket based on the file_table_names_list."""
        for i in self.file_table_names_list:
            file_location = self.raw_data_path_dir + i + self.raw_data_type
            destination_blob_name = (
                self.raw_data_bucket_path + i + self.raw_schema_file_type
            )
            # setup file to officially land
            blob = self.raw_data_bucket.blob(destination_blob_name)
            # upload the file
            blob.upload_from_filename(file_location)
            print("File {} uploaded to {}".format(file_location, destination_blob_name))

    def create_bigquery_dataset(self):
        """Create an empty dataset"""
        try:
            # setup the dataset name
            new_dataset_id = f"{self.project_name}.{self.dataset_name}"
            dataset = bigquery.Dataset(new_dataset_id)

            # Specify the geographic location where the dataset should reside.
            dataset.location = self.dataset_location

            # Send the dataset to the API for creation.
            # Raises google.api_core.exceptions.Conflict if the Dataset already
            # exists within the project.
            dataset = self.bigquery_client.create_dataset(
                dataset
            )  # Make an API request.
            print(
                "Created dataset {}.{}".format(
                    self.bigquery_client.project, dataset.dataset_id
                )
            )
        except Conflict:
            print("Dataset already exists '{}'.".format(self.dataset_name))

    def delete_bigquery_dataset(self):
        # Use the delete_contents parameter to delete a dataset and its contents.
        # Use the not_found_ok parameter to not receive an error if the dataset has already been deleted.
        self.bigquery_client.delete_dataset(
            self.dataset_name, delete_contents=True, not_found_ok=True
        )  # Make an API request.

        print("Deleted dataset '{}'.".format(self.dataset_name))

    def delete_bigquery_table(self, table_name):
        """delete a bigquery table"""
        table_ref = self.dataset.table(table_name)
        try:
            self.bigquery_client.delete_table(table_ref)
        except NotFound:
            print(f"Bigquery table does NOT exist: {table_name}")

    def validate_bigquery_table_exists(self, table_name):
        """check if the bigquery table in scope exists"""
        table_ref = self.dataset.table(table_name)
        try:
            self.bigquery_client.get_table(table_ref)
            print(f"Bigquery table exists: {table_name}")
            return True
        except NotFound:
            print(f"Bigquery table does NOT exist: {table_name}")
            return False

    def validate_gcs_file_exists(self, bucket_path, file_name):
        """check if the gcs file in scope exists"""
        try:
            # Note: Client.list_blobs requires at least package version 1.17.0.
            blobs = self.storage_client.list_blobs(bucket_path)

            for blob in blobs:
                if blob.name == file_name:
                    print(f"File exists: {file_name}")
                    return True
        except NotFound:
            print(f"File does NOT exist: {file_name}")
            return False

    def copy_single_file_gcs_to_gcs(
        self, bucket_name, blob_name, destination_bucket_name, destination_blob_name
    ):
        """COPIES a blob from one bucket to another with a new name."""
        # bucket_name = "your-bucket-name"
        # blob_name = "your-object-name"
        # destination_bucket_name = "destination-bucket-name"
        # destination_blob_name = "destination-object-name"

        source_bucket = self.storage_client.bucket(bucket_name)
        source_blob = source_bucket.blob(blob_name)
        destination_bucket = self.storage_client.bucket(destination_bucket_name)

        blob_copy = source_bucket.copy_blob(
            source_blob, destination_bucket, destination_blob_name
        )

        print(
            "Blob {} in bucket {} COPIED to blob {} in bucket {}.".format(
                source_blob.name,
                source_bucket.name,
                blob_copy.name,
                destination_bucket.name,
            )
        )

    def copy_multiple_files_gcs_to_gcs(
        self,
        files_list,
        blob_name_prefix,
        bucket_name,
        destination_bucket_name,
        destination_blob_name_prefix,
    ):
        """copy_single_file_gcs_to_gcs in a loop based on a list of file names and desired prefixes"""

        for i in files_list:
            blob_name = blob_name_prefix + i
            destination_blob_name = destination_blob_name_prefix + i
            self.copy_single_file_gcs_to_gcs(
                bucket_name, blob_name, destination_bucket_name, destination_blob_name
            )

    def move_single_file_gcs_to_gcs(
        self, bucket_name, blob_name, destination_bucket_name, destination_blob_name
    ):
        """MOVES a blob from one bucket to another with a new name."""
        # bucket_name = "your-bucket-name"
        # blob_name = "your-object-name"
        # destination_bucket_name = "destination-bucket-name"
        # destination_blob_name = "destination-object-name"

        # based on official docs, moving files requires copying AND deleting source blob after
        self.copy_single_file_gcs_to_gcs(
            bucket_name, blob_name, destination_bucket_name, destination_blob_name
        )

        # delete the source object after copying over
        self.delete_blob(bucket_name, blob_name)

    def move_multiple_files_gcs_to_gcs(
        self,
        files_list,
        blob_name_prefix,
        bucket_name,
        destination_bucket_name,
        destination_blob_name_prefix,
    ):
        """move_single_file_gcs_to_gcs in a loop based on a list of file names and desired prefixes"""

        for i in files_list:
            blob_name = blob_name_prefix + i
            destination_blob_name = destination_blob_name_prefix + i
            self.move_single_file_gcs_to_gcs(
                bucket_name, blob_name, destination_bucket_name, destination_blob_name
            )

    def delete_blob(self, bucket_name, blob_name):
        """Deletes a blob from the bucket."""
        # bucket_name = "your-bucket-name"
        # blob_name = "your-object-name"

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

        print("Blob {} deleted.".format(blob_name))

    def rename_blob(self, bucket_name, blob_name, new_name):
        """Renames a blob."""
        # bucket_name = "your-bucket-name"
        # blob_name = "your-object-name"
        # new_name = "new-object-name"

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        new_blob = bucket.rename_blob(blob, new_name)

        print("Blob {} has been renamed to {}".format(blob.name, new_blob.name))

    def list_blobs(self, bucket_name):
        """Lists all the blobs in the bucket."""
        # bucket_name = "your-bucket-name"

        # Note: Client.list_blobs requires at least package version 1.17.0.
        blobs = self.storage_client.list_blobs(bucket_name)

        for blob in blobs:
            print(blob.name)


# TODO (developer)-example commands as needed below
gcp_toolkit = gcp_utilities(utility_configs)
# gcp_toolkit.upload_raw_schemas()
# gcp_toolkit.upload_raw_data()
# gcp_toolkit.create_bigquery_dataset()
# gcp_toolkit.copy_single_file_gcs_to_gcs(
#     bucket_name="daci_npe_landing",
#     blob_name="test/assortment.json",
#     destination_bucket_name="daci_npe_landing",
#     destination_blob_name="unit_test_archive/assortment.json",
# )

# gcp_toolkit.copy_multiple_files_gcs_to_gcs(
#     files_list=files_list,
#     blob_name_prefix="unit_test_archive/",
#     bucket_name="daci_npe_landing",
#     destination_bucket_name="daci_npe_landing",
#     destination_blob_name_prefix="unit_test_archive/raw_data/",
# )

# gcp_toolkit.move_multiple_files_gcs_to_gcs(
#     files_list=files_list,
#     blob_name_prefix="unit_test_archive/",
#     bucket_name="daci_npe_landing",
#     destination_bucket_name="daci_npe_landing",
#     destination_blob_name_prefix="unit_test_archive_MOVE_test/",
# )

# gcp_toolkit.list_blobs(bucket_name="daci_npe_landing")

# gcp_toolkit.delete_bigquery_table(table_name="assortment")
# gcp_toolkit.validate_bigquery_table_exists(table_name="assortment")
# gcp_toolkit.create_bigquery_dataset()
# gcp_toolkit.delete_bigquery_dataset()
