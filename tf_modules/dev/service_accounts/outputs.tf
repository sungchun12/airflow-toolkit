output "service-account-bastion-host-email" {
    value = google_service_account.service-account-bastion-host.email
    description = "The email for the bastion host service account"
}

output "composer-worker-iam-member" {
    value = google_project_iam_member.composer-worker.id
    description = "id of the the composer worker iam member"
}

output "composer-worker-service-account" {
    value = google_service_account.service-account-composer.name
    description = "id of the the composer worker iam member"
}