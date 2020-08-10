locals {
  # Automatically load account-level variables
  account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl"))

  # Automatically load region-level variables
  region_vars = read_terragrunt_config(find_in_parent_folders("region.hcl"))

  # Automatically load environment-level variables
  environment_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))

  # Extract out common variables for reuse
  project = local.account_vars.locals.project
  region  = local.region_vars.locals.region
  zone    = local.region_vars.locals.zone
  env     = local.environment_vars.locals.environment
}

# Terragrunt will copy the Terraform configurations specified by the source parameter, along with any files in the
# working directory, into a temporary folder, and execute your Terraform commands in that folder.
terraform {
  source = "../../../../../terragrunt_infrastructure_modules//cloud_composer"
}

# Define dependencies
dependency "networking" {
  config_path = "../networking"

  mock_outputs = {
    network                       = "network"
    subnetwork                    = "subnetwork"
    cluster_secondary_range_name  = "cluster_secondary_range_name"
    services_secondary_range_name = "services_secondary_range_name"
  }

  mock_outputs_allowed_terraform_commands = ["plan", "validate"]
}

dependency "service_accounts" {
  config_path = "../service_accounts"

  mock_outputs = {
    composer-worker-service-account = "service-account-compute@developer.gserviceaccount.com"
  }

  mock_outputs_allowed_terraform_commands = ["plan", "validate"]
}

dependencies {
  paths = ["../enable_apis"]
}

# Include all settings from the root terragrunt.hcl file
include {
  path = find_in_parent_folders()
}

# These are the variables we have to pass in to use the module specified in the terragrunt configuration above
inputs = {
  project                       = "${local.project}"
  region                        = "${local.region}"
  zone                          = "${local.zone}"
  service_account               = dependency.service_accounts.outputs.composer-worker-service-account
  network                       = dependency.networking.outputs.network
  subnetwork                    = dependency.networking.outputs.subnetwork
  cluster_secondary_range_name  = dependency.networking.outputs.cluster_secondary_range_name
  services_secondary_range_name = dependency.networking.outputs.services_secondary_range_name
}
