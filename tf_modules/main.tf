# ---------------------------------------------------------------------------------------------------------------------
# ENABLE APIS
# These are expected to be passed in by the operator as a list
# This module is most useful when it depends on a brand new project deployed by terraform too
# Note: https://github.com/terraform-google-modules/terraform-google-project-factory/tree/master/modules/project_services
# Hope and pray this comes soon: https://github.com/hashicorp/terraform/issues/10462#issuecomment-527651371
# ---------------------------------------------------------------------------------------------------------------------

module "api-enable-services" {
  source  = "./dev/enable_apis"
  project = var.project
}

module "compute_engine" {
  source             = "./dev/compute_engine"
  project            = var.project
  subnetwork_id      = module.networking.subnetwork
  bastion_host_email = module.service_accounts.service-account-bastion-host-email
  # depends_on         = [module.api-enable-services] #TODO(developer): uncomment once version v0.13.0 is in GA, terragrunt handles module dependencies for now
}

module "cloud_composer" {
  source                        = "./dev/cloud_composer"
  project                       = var.project
  network                       = module.networking.network
  subnetwork                    = module.networking.subnetwork
  service_account               = module.service_accounts.composer-worker-service-account
  cluster_secondary_range_name  = module.networking.cluster_secondary_range_name
  services_secondary_range_name = module.networking.services_secondary_range_name
  # depends_on           = [module.service_accounts.composer-worker-iam-member, module.api-enable-services] #TODO(developer): uncomment once version v0.13.0 is in GA, terragrunt handles module dependencies for now
}

module "networking" {
  project = var.project
  source  = "./dev/networking"
}

module "service_accounts" {
  source  = "./dev/service_accounts"
  project = var.project
}
