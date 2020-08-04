module "api-enable-services" {
  source                      = "terraform-google-modules/project-factory/google//modules/project_services" #variables not allowed here
  version                     = "4.0.0"                                                                     #variables not allowed here
  project_id                  = var.project
  activate_apis               = var.api_services
  disable_services_on_destroy = var.disable_services_on_destroy_bool
  enable_apis                 = var.enable_apis_bool
}