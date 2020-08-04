output "secondary_range_names" {
  value       = [for i in google_compute_subnetwork.subnetwork-composer.secondary_ip_range : i["range_name"]]
  description = "The names of the secondary ranges being created in one subnet"
}

output "network" {
    value = google_compute_network.network-composer.id
    description = "The exact id for the vpc network"
}

output "subnetwork" {
    value = google_compute_subnetwork.subnetwork-composer.id
    description = "The exact id for the vpc subnetwork"
}

output "cluster_secondary_range_name" {
    value = google_compute_subnetwork.subnetwork-composer.secondary_ip_range[0]["range_name"]
    description = "The exact id for the vpc subnetwork"
}

output "services_secondary_range_name" {
    value = google_compute_subnetwork.subnetwork-composer.secondary_ip_range[1]["range_name"]
    description = "The exact id for the vpc subnetwork"
}