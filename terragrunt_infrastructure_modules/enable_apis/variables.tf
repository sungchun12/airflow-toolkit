# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# These variables are expected to be passed in by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "project" {
  type    = string
  default = ""
}

# ---------------------------------------------------------------------------------------------------------------------
# OPTIONAL MODULE PARAMETERS
# These variables have defaults, but may be overridden by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "api_services" {
  description = "list of Google Cloud apis to enable when launching terraform"
  type        = list(string)
  default     = ["datafusion.googleapis.com", "composer.googleapis.com"]
}

variable "disable_services_on_destroy_bool" {
  description = "whether project services will be disabled when the resources are destroyed"
  type        = string
  default     = "false"
}

variable "enable_apis_bool" {
  description = "whether to actually enable the APIs. If false, this module is a no-op"
  type        = string
  default     = "true"
}
