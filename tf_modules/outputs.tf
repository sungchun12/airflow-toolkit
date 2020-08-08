output "cloud_composer_id" {
  description = "The exact id of the cloud composer environment"
  value       = module.cloud_composer.cloud_composer_id
}

output "cloud_composer_gke_cluster" {
  description = "The exact id of the Kubernetes Engine cluster used to run this environment"
  value       = module.cloud_composer.cloud_composer_gke_cluster
}

output "cloud_composer_dags_gcs_prefix" {
  description = "The Cloud Storage prefix of the DAGs for this environment. Although Cloud Storage objects reside in a flat namespace, a hierarchical file tree can be simulated using '/'-delimited object name prefixes. DAG objects for this environment reside in a simulated directory with this prefix."
  value       = module.cloud_composer.cloud_composer_dags_gcs_prefix
}

output "cloud_composer_airflow_uri" {
  description = "The URI of the Apache Airflow Web UI hosted within this environment."
  value       = module.cloud_composer.cloud_composer_airflow_uri
}

output "compute_engine_id" {
  description = "The exact id of the compute engine id"
  value       = module.compute_engine.compute_engine_id
}

output "compute_engine_nat_ip" {
  description = "The external IP of the compute engine instance"
  value       = module.compute_engine.compute_engine_nat_ip
}

output "network" {
  description = "The exact id for the vpc network"
  value       = module.networking.network
}

output "subnetwork" {
  description = "The exact id for the vpc subnetwork"
  value       = module.networking.subnetwork
}

output "cluster_secondary_range_name" {
  description = "The exact id for the cluster/pods secondary range name"
  value       = module.networking.cluster_secondary_range_name
}

output "services_secondary_range_name" {
  description = "The exact id for the services secondary range name"
  value       = module.networking.services_secondary_range_name
}

output "service-account-bastion-host-email" {
  description = "The email for the bastion host service account"
  value       = module.service_accounts.service-account-bastion-host-email
}

output "composer-worker-iam-member" {
  description = "id of the the composer worker iam member"
  value       = module.service_accounts.composer-worker-iam-member
}

output "composer-worker-service-account" {
  description = "name of the the composer worker service account"
  value       = module.service_accounts.composer-worker-service-account
}
