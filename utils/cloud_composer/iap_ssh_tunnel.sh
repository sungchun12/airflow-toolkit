#!/bin/bash

# simple utility to enable the service account and tunnel
# into the the bastion host through identity access proxy

# setup the higher access service account to do the below operations
ACCESS_KEY_FILE="service_account.json"
gcloud auth activate-service-account --key-file=$ACCESS_KEY_FILE

# set project config
PROJECT_ID="wam-bam-258119"
gcloud config set project $PROJECT_ID

# enable the service account
SERVICE_ACCOUNT_EMAIL="iap-ssh-sa-dev@wam-bam-258119.iam.gserviceaccount.com"
gcloud beta iam service-accounts enable $SERVICE_ACCOUNT_EMAIL

# download a private json key
gcloud iam service-accounts keys create iap-ssh-access-sa.json \
--iam-account=$SERVICE_ACCOUNT_EMAIL \
--key-file-type="json"

# set service account config in terminal
KEY_FILE="iap-ssh-access-sa.json"
gcloud auth activate-service-account --key-file=$KEY_FILE

# ssh tunnel into the bastion host
BASTION_HOST="bastion-host-to-composer"
ZONE="us-central1-b"
gcloud compute ssh $BASTION_HOST --tunnel-through-iap --zone $ZONE