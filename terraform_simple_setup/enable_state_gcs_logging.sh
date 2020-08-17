#!/bin/bash

# OPTIONAL: store log files of operations on the backend state bucket within gcs
gsutil mb gs://tfstate-logs-bucket

gsutil iam ch group:cloud-storage-analytics@google.com:legacyBucketWriter gs://tfstate-logs-bucket

gsutil logging set on -b gs://tfstate-logs-bucket -o dev gs://secure-bucket-tfstate-composer