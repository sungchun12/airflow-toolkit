# ---------------------------------------------------------------------------------------------------------------------
# DEPLOY COMPUTE ENGINE BASTION HOST TO RUN COMMANDS AGAINST THE CLOUD COMPOSER KUBERNETES CLUSTER
# ---------------------------------------------------------------------------------------------------------------------

# Minimal Setup
resource "google_compute_instance" "bastion-host-to-composer" {
  project      = var.project
  name         = var.name
  machine_type = var.machine_type
  zone         = var.zone

  tags = var.tags

  boot_disk {
    initialize_params {
      image = var.image
    }
  }

  scratch_disk {
    interface = var.interface
  }

  network_interface {
    subnetwork = var.subnetwork_id

    access_config {
      // Ephemeral IP
    }
  }

  metadata = var.metadata

  metadata_startup_script = var.metadata_startup_script

  service_account {
    email  = var.bastion_host_email
    scopes = var.scopes
  }
}
