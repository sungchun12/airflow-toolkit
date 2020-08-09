output "service-account-bastion-host-email" {
  description = "The email for the bastion host service account"
  value       = google_service_account.service-account-bastion-host.email
}

output "composer-worker-iam-member" {
  description = "id of the the composer worker iam member"
  value       = google_project_iam_member.composer-worker.id
}

output "composer-worker-service-account" {
  description = "name of the the composer worker service account"
  value       = google_service_account.service-account-composer.name
}
