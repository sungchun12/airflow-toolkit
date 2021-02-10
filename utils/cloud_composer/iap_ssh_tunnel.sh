#!/bin/bash

# simple utility to enable the service account and tunnel
# into the the bastion host through identity access proxy

# setup the higher access service account to do the below operations
gcloud auth activate-service-account --key-file=$ACCESS_KEY_FILE

# set project config
gcloud config set project $PROJECT_ID

# enable the service account
gcloud beta iam service-accounts enable $SERVICE_ACCOUNT_EMAIL

# download a private json key
gcloud iam service-accounts keys create $KEY_FILE \
--iam-account=$SERVICE_ACCOUNT_EMAIL \
--key-file-type="json"

# set service account config in terminal
gcloud auth activate-service-account --key-file=$KEY_FILE

# ssh tunnel into the bastion host
BASTION_HOST="bastion-host-to-composer"
gcloud compute ssh $BASTION_HOST --tunnel-through-iap --zone $ZONE