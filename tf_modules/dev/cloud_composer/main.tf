# ---------------------------------------------------------------------------------------------------------------------
# SETUP PRIVATE IP CLOUD COMPOSER
# ---------------------------------------------------------------------------------------------------------------------

# https://cloud.google.com/composer/docs/how-to/managing/creating#access-control
# generic examples, may not use actual content listed
# another example config: https://github.com/jaketf/terraform-composer-private-ip/blob/master/config/composer_config.json
// subnet:   192.169.30.0/20
// services: 172.16.16.0/24
// pods:     172.16.0.0/20
// master:   192.168.70.0/28

// webserver: 172.31.245.0/24 # default IP range
// cloud sql: 10.0.0.0/12 # default IP range

// mentioned some concerns around routing and IP overlap. Cloud composer is basically the same as GKE in terms of networking. The main difference is that the UI is running in a tenant project. If IP overlap is a concern I would recommend you create the secondary ranges on their subnet so it's not up to Google

// I'd also say watch out for the master IP range since it's easy to have IP overlap there – the master IPs are assigned in the tenant project and routable through VPC peering. I've seen a few cases where teams get IP overlap because they don't set aside an IP range for masters. For example, a core IaaS team cut out a block of unused IPs for masters and hand out a /28 for each GKE cluster or composer instance

#     One other thing  – I'd go big on the pod IP range if you can. IIRC the nodes will each want 256 IPs from the pod IP range. So if you have e.g. a /21 pod range you'll only get 8 nodes max, even if your subnet's primary IP range has space for nodes
# ​
#     You can change max-pods-per-node or add a second node pool in GKE to fix it but IDK about composer

resource "google_composer_environment" "dev-composer" {
  provider = google-beta
  name     = "dev-composer"
  region   = "us-central1"
  labels   = { "environment" : "dev" }
  config {
    node_count = 3
    node_config {
      zone         = "us-central1-b"
      machine_type = "n1-standard-1"
      #   network         = google_compute_network.network-composer.id
      network = var.network
      #   subnetwork      = google_compute_subnetwork.subnetwork-composer.id
      subnetwork   = var.subnetwork
      disk_size_gb = 100
      oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
      #   service_account = google_service_account.service-account-composer.name
      service_account = var.service_account

      ip_allocation_policy {
        use_ip_aliases = true
        # TODO: have to create dedicated and named subnets. If I manually assign here, it will be deleted on the next terraform apply
        # cluster_secondary_range_name  = google_compute_subnetwork.subnetwork-composer.secondary_ip_range[0]["range_name"]
        cluster_secondary_range_name = var.cluster_secondary_range_name
        # services_secondary_range_name = google_compute_subnetwork.subnetwork-composer.secondary_ip_range[1]["range_name"]
        services_secondary_range_name = var.services_secondary_range_name
      }
    }

    # airflow specific configs
    software_config {
      image_version = "composer-1.11.0-airflow-1.10.9"

      airflow_config_overrides = {
        core-load_example = "True"
      }

      pypi_packages = {
        numpy      = ""
        scipy      = "==1.1.0"
        kubernetes = "==11.0.0"
        pytest     = "==5.4.3"
      }

      env_variables = {
        environment = "dev"
      }

      python_version = "3"
    }

    private_environment_config {
      enable_private_endpoint    = true # applies to the kubernetes cluster, NOT airflow UI webserver
      master_ipv4_cidr_block     = "192.168.70.0/28"
      cloud_sql_ipv4_cidr_block  = "10.0.0.0/12"     # default IP range
      web_server_ipv4_cidr_block = "172.31.245.0/24" # default IP range
    }

    # default access
    web_server_network_access_control {
      allowed_ip_range {
        description = "Allows access from all IPv4 addresses (default value)"
        value       = "0.0.0.0/0"
      }
      allowed_ip_range {
        description = "Allows access from all IPv6 addresses (default value)"
        value       = "::0/0"
      }
    }
  }
  #   depends_on = [google_project_iam_member.composer-worker, module.api-enable-services]
  #   depends_on = var.composer_depends_on
}
