
# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# These variables are expected to be passed in by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "credentials" {
  description = "path to service account json file"
  type        = string
  default     = "service_account.json"
}

variable "project" {
  description = "name of your GCP project"
  type        = string
  default     = "big-demo-dreams"
}

variable "location" {
  description = "default location of various GCP services"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "default granular location typically for VMs"
  type        = string
  default     = "us-central1-b"
}

variable "service_account_email" {
  description = "Service account used for VMs"
  type        = string
  default     = "demo-service-account@big-demo-dreams.iam.gserviceaccount.com"
}

variable "version_label" {
  description = "helpful label to version GCP resources per deployment"
  type        = string
  default     = "demo"
}
