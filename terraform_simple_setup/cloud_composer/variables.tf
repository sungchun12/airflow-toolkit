# ---------------------------------------------------------------------------------------------------------------------
# REQUIRED PARAMETERS
# These variables are expected to be passed in by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "project" {
  description = "project where terraform will setup these services"
  type        = string
}

variable "region" {
  description = "Region where cloud composer will be deployed"
  type        = string
}

variable "zone" {
  description = "Specific zone where cloud composer will be deployed"
  type        = string
}

variable "network" {
  description = "VPC Network where cloud composer will be setup"
  type        = string
}

variable "subnetwork" {
  description = "Subnetwork where cloud composer will be setup"
  type        = string
}

variable "service_account" {
  description = "Service account to assign the cloud composer environment, typically to setup composer worker permissions"
  type        = string
}

variable "cluster_secondary_range_name" {
  description = "IP address range for the Kubernetes pods"
  type        = string
}

variable "services_secondary_range_name" {
  description = "IP address range for the Kubernetes services within the cluster"
  type        = string
}

# ---------------------------------------------------------------------------------------------------------------------
# OPTIONAL MODULE PARAMETERS
# These variables have defaults, but may be overridden by the operator
# ---------------------------------------------------------------------------------------------------------------------
variable "name" {
  description = "Name of the cloud composer instance"
  type        = string
  default     = "dev-composer"
}

variable "labels" {
  description = "Labels for the cloud composer environment"
  type        = map(string)
  default     = { "environment" : "dev" }
}

variable "node_count" {
  description = "Number of nodes"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Follow compute engine machine types"
  type        = string
  default     = "n1-standard-1"
}

variable "disk_size_gb" {
  description = "Disk size associated with the nodes"
  type        = number
  default     = 100
}

# you should NOT have to change this default
variable "oauth_scopes" {
  description = "Determine which services cloud composer is allowed to interact with"
  type        = list(string)
  default     = ["https://www.googleapis.com/auth/cloud-platform"]
}

variable "use_ip_aliases" {
  description = "Cloud storage bucket location for dataflow job"
  type        = bool
  default     = true
}

variable "image_version" {
  description = "Specify composer and airflow image version"
  type        = string
  default     = "composer-1.11.0-airflow-1.10.9"
}

variable "airflow_config_overrides" {
  description = "Airflow config overrides"
  type        = map(string)
  default = {
    core-load_example = "False"
  }
}

variable "pypi_packages" {
  description = "Python packages to be downloaded from the public internet"
  type        = map(string)
  default = {
    numpy  = ""
    scipy  = "==1.1.0"
    pytest = "==5.4.3"
  }
}

variable "env_variables" {
  description = "Environment variables within the composer environment"
  type        = map(string)
  default = {
    environment = "dev"
  }
}

variable "python_version" {
  description = "Python version to use. Keep in mind Python 2 is depracated now."
  type        = string
  default     = "3"
}

# this should generally be true
variable "enable_private_endpoint" {
  description = "Make composer primarily work within internal internet infrastructure"
  type        = bool
  default     = true
}

# https://tools.ietf.org/html/rfc1918
variable "master_ipv4_cidr_block" {
  description = "Private IP that follows range options compliant with RFC 1918"
  type        = string
  default     = "192.168.70.0/28"
}

variable "cloud_sql_ipv4_cidr_block" {
  description = "Private IP that follows range options compliant with RFC 1918. This is a Google-specific default for cloud sql."
  type        = string
  default     = "10.0.0.0/12"
}

variable "web_server_ipv4_cidr_block" {
  description = "Private IP that follows range options compliant with RFC 1918. This is a Google-specific default for the web server."
  type        = string
  default     = "172.31.245.0/24"
}

variable "allowed_ip_ranges" {
  description = "This is a Google-specific default for the web server, and allows any public internet access through identity aware proxy."
  type        = list(any)
  default = [
    {
      description = "Allows access from all IPv4 addresses (default value)"
      value       = "0.0.0.0/0"
    },
    {
      description = "Allows access from all IPv6 addresses (default value)"
      value       = "::0/0"
    },
  ]
}
