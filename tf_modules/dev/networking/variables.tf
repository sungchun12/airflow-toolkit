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
variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "composer-dev-network"
}

variable "network_description" {
  description = "VPC network description"
  type        = string
  default     = "VPC network just for cloud composer"
}

variable "auto_create_subnetworks" {
  description = "Whether to auto-create subnetworks in VPC or not"
  type        = bool
  default     = false
}

variable "routing_mode" {
  description = "Routing at the geography level"
  type        = string
  default     = "REGIONAL"
}

variable "subnetwork_name" {
  description = "VPC subnetwork name"
  type        = string
  default     = "composer-dev-subnetwork"
}

variable "ip_cidr_range" {
  description = "VPC subnetwork internal ip range"
  type        = string
  default     = "10.2.0.0/16"
}

variable "subnetwork_region" {
  description = "VPC subnetwork region"
  type        = string
  default     = "us-central1"
}

variable "secondary_ip_range" {
  description = "List of maps related to cluster and services secondary ip ranges"
  type        = list(any)
  # cluster and services ip ranges but be listed in this exact order
  default = [
    {
      ip_cidr_range = "172.16.0.0/20" # cluster
      range_name    = "gke-cluster"
    },
    {
      ip_cidr_range = "172.16.16.0/24" # services
      range_name    = "gke-services"
    },
  ]
}

variable "private_ip_google_access" {
  description = "Whether to enable private ip google access or not"
  type        = bool
  default     = true
}

variable "firewall_name" {
  description = "Firewall name"
  type        = string
  default     = "dev-bastion-ssh-firewall"
}

variable "firewall_description" {
  description = "Firewall description"
  type        = string
  default     = "Allow IAP to connect to VM instances"
}

variable "firewall_direction" {
  description = "Firewall direction"
  type        = string
  default     = "INGRESS"
}

variable "firewall_priority" {
  description = "Firewall priority"
  type        = number
  default     = 1000
}
