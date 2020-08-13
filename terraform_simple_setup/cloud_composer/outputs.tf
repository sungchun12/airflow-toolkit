output "cloud_composer_id" {
  description = "The exact id of the cloud composer environment"
  value       = google_composer_environment.cloud-composer-env.id
}

output "cloud_composer_gke_cluster" {
  description = "The exact id of the Kubernetes Engine cluster used to run this environment"
  value       = google_composer_environment.cloud-composer-env.config[0].gke_cluster
}

output "cloud_composer_dags_gcs_prefix" {
  description = "The Cloud Storage prefix of the DAGs for this environment. Although Cloud Storage objects reside in a flat namespace, a hierarchical file tree can be simulated using '/'-delimited object name prefixes. DAG objects for this environment reside in a simulated directory with this prefix"
  value       = google_composer_environment.cloud-composer-env.config[0].dag_gcs_prefix
}

output "cloud_composer_airflow_uri" {
  description = "The URI of the Apache Airflow Web UI hosted within this environment"
  value       = google_composer_environment.cloud-composer-env.config[0].airflow_uri
}
