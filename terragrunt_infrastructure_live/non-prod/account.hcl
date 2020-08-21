
# Set account-wide variables. These are automatically pulled in to configure the remote state bucket in the root
# terragrunt.hcl configuration.
locals {
  project               = "wam-bam-258119"
  service_account_email = "demo-v2@wam-bam-258119.iam.gserviceaccount.com"
}
