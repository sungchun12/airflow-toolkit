# ---------------------------------------------------------------------------------------------------------------------
# SETUP PRIVATE IP CLOUD COMPOSER
# ---------------------------------------------------------------------------------------------------------------------

resource "google_composer_environment" "cloud-composer-env" {
  project  = var.project
  provider = google-beta
  name     = var.name
  region   = var.region
  labels   = var.labels

  config {
    node_count = var.node_count

    node_config {
      zone            = var.zone
      machine_type    = var.machine_type
      network         = var.network
      subnetwork      = var.subnetwork
      disk_size_gb    = var.disk_size_gb
      oauth_scopes    = var.oauth_scopes
      service_account = var.service_account

      ip_allocation_policy {
        use_ip_aliases                = var.use_ip_aliases
        cluster_secondary_range_name  = var.cluster_secondary_range_name
        services_secondary_range_name = var.services_secondary_range_name
      }
    }

    # airflow specific configs
    software_config {
      image_version            = var.image_version
      airflow_config_overrides = var.airflow_config_overrides
      pypi_packages            = var.pypi_packages
      env_variables            = var.env_variables
      python_version           = var.python_version
    }

    private_environment_config {
      enable_private_endpoint    = var.enable_private_endpoint # applies to the kubernetes cluster, NOT airflow UI webserver
      master_ipv4_cidr_block     = var.master_ipv4_cidr_block
      cloud_sql_ipv4_cidr_block  = var.cloud_sql_ipv4_cidr_block  # default IP range
      web_server_ipv4_cidr_block = var.web_server_ipv4_cidr_block # default IP range
    }

    # default access, but built for dynamic ip range blocks
    web_server_network_access_control {
      dynamic "allowed_ip_range" {
        for_each = [for s in var.allowed_ip_ranges : {
          description = s.description
          value       = s.value
        }]

        content {
          description = allowed_ip_range.value.description
          value       = allowed_ip_range.value.value
        }
      }
    }
  }
}
