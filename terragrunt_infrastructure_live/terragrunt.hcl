locals {
  # Automatically load account-level variables
  account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl"))

  # Automatically load region-level variables
  region_vars = read_terragrunt_config(find_in_parent_folders("region.hcl"))

  # Automatically load environment-level variables
  environment_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))

  # Extract the variables we need for easy access
  project               = local.account_vars.locals.project
  service_account_email = local.account_vars.locals.project
  region                = local.region_vars.locals.region
  zone                  = local.region_vars.locals.zone
  environment           = local.environment_vars.locals.environment

  # Extract gitignored service account credentials json file
  # When run in CICD, this file will NOT persist
  # Secrets are written to a temporary file in case different privileges are required across modules
  # Minimizes the secrets manager API calls by NOT individually setting each credentials var with the API call
  credentials      = run_cmd("--terragrunt-quiet", "${get_parent_terragrunt_dir()}/get_secret.sh")
  credentials_file = "${get_terragrunt_dir()}/service_account.json"
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
# ---------------------------------------------------------------------------------------------------------------------
# SETUP PROVIDER DEFAULTS
# These variables are expected to be passed in by the operator
# You are expected to provide your own service account JSON file in the root module directory
# Note: The "google-beta" provider needs to be setup in ADDITION to the "google" provider
# ---------------------------------------------------------------------------------------------------------------------
provider "google" {
  credentials = "${local.credentials_file}"
  project     = "${local.project}"
  region      = "${local.region}"
  zone        = "${local.zone}"
  version     = "~> 3.34.0"
}

provider "google-beta" {
  credentials = "${local.credentials_file}"
  project     = "${local.project}"
  region      = "${local.region}"
  zone        = "${local.zone}"
  version     = "~> 3.34.0"
}
EOF
}

# automatically creates the gcs bucket
# TODO(developer): must be a unique name, so the default bucket value below will error out for you
remote_state {
  backend = "gcs"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    project     = "${local.project}"
    location    = "${local.region}"
    credentials = "${local.credentials_file}"
    bucket      = "demo-secure-bucket-tfstate-airflow-infra-${local.region}"
    prefix      = "${path_relative_to_include()}"
  }
}

generate "versions" {
  path      = "versions.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "<4.0,>= 2.12"
    }
    google-beta = {
      source = "hashicorp/google-beta"
      version = "<4.0,>= 2.12"
    }
  }
  required_version = ">= 0.13"
}

EOF
}

# ---------------------------------------------------------------------------------------------------------------------
# GLOBAL PARAMETERS
# These variables apply to all configurations in this subfolder. These are automatically merged into the child
# `terragrunt.hcl` config via the include block.
# ---------------------------------------------------------------------------------------------------------------------

# Configure root level variables that all resources can inherit. This is especially helpful with multi-account configs
# where terraform_remote_state data sources are placed directly into the modules.
inputs = merge(
  local.account_vars.locals,
  local.region_vars.locals,
  local.environment_vars.locals,
)
