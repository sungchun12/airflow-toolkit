# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# These variables are expected to be passed in by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "project" {
  description = "project where terraform will setup these services"
  type        = string
}

# ---------------------------------------------------------------------------------------------------------------------
# OPTIONAL MODULE PARAMETERS
# These variables have defaults, but may be overridden by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "account_id_bastion_host" {
  description = "Service account, account id for the bastion host"
  type        = string
  default     = "bastion-host-dev-account"
}

variable "display_name_bastion_host" {
  description = "Display name for the bastion host service account"
  type        = string
  default     = "Dev Service Account for accessing Composer Environment through bastion host"
}

variable "description_bastion_host" {
  description = "Description for the bastion host service account"
  type        = string
  default     = "Service account for dev purposes to access a private Composer Environment and run airflow/kubectl cli commands"
}

variable "account_id_iap_ssh" {
  description = "Service account, account id for identity aware proxy ssh enablement"
  type        = string
  default     = "service-account-iap-ssh"
}

variable "display_name_iap_ssh" {
  description = "Display name for the iap ssh service account"
  type        = string
  default     = "A service account that can only ssh tunnel into the VM that then can access private IP composer"
}

variable "description_iap_ssh" {
  description = "Description for the iap ssh service account"
  type        = string
  default     = "look at display name"
}

variable "account_id_composer" {
  description = "Service account, account id for the composer workers"
  type        = string
  default     = "composer-dev-account"
}

variable "display_name_composer" {
  description = "Display name for the composer workers service account"
  type        = string
  default     = "Dev Service Account for Composer Environment"
}

variable "description_composer" {
  description = "Description name for the composer workers service account"
  type        = string
  default     = "Service account for dev purposes to get a private Composer Environment running successfully"
}

# https://www.terraform.io/docs/providers/google/r/google_service_account_iam.html
# add composer specific permissions
# these are roles are too granular to add
# composer.environments.get
# container.clusters.get
# container.clusters.list
# container.clusters.getCredentials
variable "bastion_service_account_roles_to_add" {
  description = "Additional roles to be added to the service account."
  type        = list(string)
  default     = []
}

variable "ssh_service_account_roles_to_add" {
  description = "Additional roles to be added to the service account."
  type        = list(string)
  default     = []
}
