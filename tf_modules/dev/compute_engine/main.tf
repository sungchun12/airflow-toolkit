########## VM SETUP BEGINS ###############
resource "google_compute_instance" "bastion-host-to-composer" {
  name         = "bastion-host-to-composer"
  machine_type = "n1-standard-1"
  zone         = "us-central1-a"

  tags = ["dev"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  // Local SSD disk
  scratch_disk {
    interface = "SCSI"
  }

  network_interface {
    # subnetwork = google_compute_subnetwork.subnetwork-composer.id
    subnetwork = var.subnetwork_id

    access_config {
      // Ephemeral IP
    }
  }

  metadata = {
    block-project-ssh-keys = false
  }

  metadata_startup_script = "echo hi > /test.txt"

  service_account {
    # email  = google_service_account.service-account-bastion-host.email
    email = var.bastion_host_email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}