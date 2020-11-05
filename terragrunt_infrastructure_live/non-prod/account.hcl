
# Set account-wide variables. These are automatically pulled in to configure the remote state bucket in the root
# terragrunt.hcl configuration.
locals {
  project               = "big-dreams-please"
  service_account_email = "demo-service-account@big-dreams-please.iam.gserviceaccount.com"
}
