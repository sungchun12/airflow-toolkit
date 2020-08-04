#  https://cloud.google.com/vpc/docs/vpc#valid-ranges
resource "google_compute_network" "network-composer" {
  name                    = "composer-dev-network"
  description             = "VPC network just for cloud composer"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "subnetwork-composer" {
  name          = "composer-dev-subnetwork"
  ip_cidr_range = "10.2.0.0/16"
  region        = "us-central1"
  network       = google_compute_network.network-composer.id

  secondary_ip_range = [
    {
      ip_cidr_range = "172.16.0.0/20" # cluster
      range_name    = "gke-cluster"
    },
    {
      ip_cidr_range = "172.16.16.0/24" # services
      range_name    = "gke-services"
    },
  ]

  private_ip_google_access = true
}

resource "google_compute_firewall" "iap-ssh-access" {
  name        = "dev-bastion-ssh-firewall"
  network     = google_compute_network.network-composer.id
  description = "Allow IAP to connect to VM instances"
  direction   = "INGRESS"
  priority    = 1000

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
}
