# ---------------------------------------------------------------------------------------------------------------------
# ENABLE APIS
# These are expected to be passed in by the operator as a list
# This module is most useful when it depends on a brand new project deployed by terraform too
# Note: https://github.com/terraform-google-modules/terraform-google-project-factory/tree/master/modules/project_services
# Hope and pray this comes soon: https://github.com/hashicorp/terraform/issues/10462#issuecomment-527651371
# ---------------------------------------------------------------------------------------------------------------------

module "api-enable-services" {
  source                      = "terraform-google-modules/project-factory/google//modules/project_services" #variables not allowed here
  version                     = "4.0.0"                                                                     #variables not allowed here
  project_id                  = var.project
  activate_apis               = var.api_services
  disable_services_on_destroy = var.disable_services_on_destroy_bool
  enable_apis                 = var.enable_apis_bool
}
