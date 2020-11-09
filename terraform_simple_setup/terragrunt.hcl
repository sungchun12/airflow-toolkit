terraform {
  extra_arguments "common_vars" {
    commands = ["plan", "apply"]
    arguments = [
      "-var-file=common.tfvars",
    ]
  }

  before_hook "before_hook" {
    commands = ["apply", "plan"]
    execute  = ["echo", "Running Terraform"]
  }

  after_hook "after_hook" {
    commands     = ["apply", "plan"]
    execute      = ["echo", "Finished running Terraform"]
    run_on_error = true
  }
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
    project     = "big-demo-dreams"
    location    = "US"
    credentials = "service_account.json"
    bucket      = "simple-dreams-secure-bucket-tfstate-composer"
    prefix      = "dev"
  }
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
  credentials = var.credentials
  project     = var.project
  region      = var.location
  zone        = var.zone
  version     = "~> 3.34.0"
}

provider "google-beta" {
  credentials = var.credentials
  project     = var.project
  region      = var.location
  zone        = var.zone
  version     = "~> 3.34.0"
}
EOF
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
