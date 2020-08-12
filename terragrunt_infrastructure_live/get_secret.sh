#!/bin/bash
# gcloud secrets versions access latest --secret='terraform-secret'
export GOOGLE_CREDENTIALS=$(gcloud secrets versions access latest --secret='terraform-secret')