# ---------------------------------------------------------------------------------------------------------------------
# DEPLOY NETWORKING FOR CLOUD COMPOSER SETUP
# ---------------------------------------------------------------------------------------------------------------------

#  https://cloud.google.com/vpc/docs/vpc#valid-ranges
resource "google_compute_network" "network-composer" {
  project                 = var.project
  name                    = var.network_name
  description             = var.network_description
  auto_create_subnetworks = var.auto_create_subnetworks
  routing_mode            = var.routing_mode
}

resource "google_compute_subnetwork" "subnetwork-composer" {
  project       = var.project
  name          = var.subnetwork_name
  ip_cidr_range = var.ip_cidr_range
  region        = var.subnetwork_region
  network       = google_compute_network.network-composer.id

  secondary_ip_range = var.secondary_ip_range

  private_ip_google_access = var.private_ip_google_access
}

resource "google_compute_firewall" "iap-ssh-access" {
  project     = var.project
  name        = var.firewall_name
  network     = google_compute_network.network-composer.id
  description = var.firewall_description
  direction   = var.firewall_direction
  priority    = var.firewall_priority

  # the below defaults are hard-coded as these are specific to identity aware proxy ssh enablement
  # for more custom configs, you will have to make the below dynamic
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
}
