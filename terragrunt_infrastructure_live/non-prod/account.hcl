
# Set account-wide variables. These are automatically pulled in to configure the remote state bucket in the root
# terragrunt.hcl configuration.
locals {
  project               = "big-demo-dreams"
  service_account_email = "demo-service-account@big-demo-dreams.iam.gserviceaccount.com"
}
