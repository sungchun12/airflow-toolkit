output "compute_engine_id" {
  description = "The exact id of the compute engine id"
  value       = google_compute_instance.bastion-host-to-composer.id
}

output "compute_engine_nat_ip" {
  description = "The external IP of the compute engine instance"
  value       = google_compute_instance.bastion-host-to-composer.network_interface[0].access_config[0].nat_ip
}
