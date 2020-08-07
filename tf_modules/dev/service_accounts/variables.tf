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
