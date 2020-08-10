# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEPLOY A COMPREHENSIVE CLOUD COMPOSER ENVIRONMENT WITH SUPPORTING INFRASTRUCTURE AND NETWORKING
# This module serves as the main interface for all the supporting modules
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ---------------------------------------------------------------------------------------------------------------------
# IMPORT MODULES
# This root module imports and passes through project wide variables
# Detailed default variables contained within respective module directory
# -------------------------------------------------------------------------------------------------------------------
module "api-enable-services" {
  source  = "./enable_apis"
  project = var.project
}

module "compute_engine" {
  source             = "./compute_engine"
  project            = var.project
  subnetwork_id      = module.networking.subnetwork
  bastion_host_email = module.service_accounts.service-account-bastion-host-email
  # depends_on         = [module.api-enable-services] #TODO(developer): uncomment once version v0.13.0 is in GA, terragrunt handles module dependencies for now
}

module "cloud_composer" {
  source                        = "./cloud_composer"
  project                       = var.project
  region                        = var.location
  zone                          = var.zone
  network                       = module.networking.network
  subnetwork                    = module.networking.subnetwork
  service_account               = module.service_accounts.composer-worker-service-account
  cluster_secondary_range_name  = module.networking.cluster_secondary_range_name
  services_secondary_range_name = module.networking.services_secondary_range_name
  # depends_on           = [module.service_accounts.composer-worker-iam-member, module.api-enable-services] #TODO(developer): uncomment once version v0.13.0 is in GA, terragrunt handles module dependencies for now
}

module "networking" {
  source  = "./networking"
  project = var.project
}

module "service_accounts" {
  source  = "./service_accounts"
  project = var.project
}
