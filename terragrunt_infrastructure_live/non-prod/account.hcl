
# Set account-wide variables. These are automatically pulled in to configure the remote state bucket in the root
# terragrunt.hcl configuration.
locals {
  project               = "airflow-demo-build"
  service_account_email = "airflow-test@airflow-demo-build.iam.gserviceaccount.com"
}
