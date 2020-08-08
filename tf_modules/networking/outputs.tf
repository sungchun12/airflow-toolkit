output "network" {
  description = "The exact id for the vpc network"
  value       = google_compute_network.network-composer.id
}

output "subnetwork" {
  description = "The exact id for the vpc subnetwork"
  value       = google_compute_subnetwork.subnetwork-composer.id
}

output "cluster_secondary_range_name" {
  description = "The exact id for the cluster/pods secondary range name"
  value       = google_compute_subnetwork.subnetwork-composer.secondary_ip_range[0]["range_name"]
}

output "services_secondary_range_name" {
  description = "The exact id for the services secondary range name"
  value       = google_compute_subnetwork.subnetwork-composer.secondary_ip_range[1]["range_name"]
}
