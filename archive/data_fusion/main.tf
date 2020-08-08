# ---------------------------------------------------------------------------------------------------------------------
# SETUP DATA FUSION SIMPLE ENTERPRISE INSTANCE
# ---------------------------------------------------------------------------------------------------------------------
# # https://www.terraform.io/docs/providers/google/r/data_fusion_instance.html#private_instance
# NOT able to select specific version such "6.1.3"
resource "google_data_fusion_instance" "demo_instance" {
  provider                      = google-beta
  name                          = "demo-instance"
  description                   = "Demo Data Fusion instance"
  region                        = "us-central1"
  type                          = "ENTERPRISE"
  enable_stackdriver_logging    = false
  enable_stackdriver_monitoring = false
  timeouts {
    create = "1.5h"
  }
  # private_instance = true

  # network_config {
  #   network = "default"
  #   ip_allocation = "10.89.48.0/22"
  # }

  #   depends_on = [module.api-enable-services]
}
