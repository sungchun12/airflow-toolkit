#!/bin/bash

gcloud config set project $PROJECT_ID
export TERRAFORM_SECRET=$(gcloud secrets versions access latest --secret='terraform-secret')
echo $TERRAFORM_SECRET > service_account.json