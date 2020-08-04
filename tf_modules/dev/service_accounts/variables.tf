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