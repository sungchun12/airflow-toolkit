# https://www.terraform.io/docs/providers/google/r/google_service_account_iam.html
# add composer specific permissions
# these are roles are too granular to add
# composer.environments.get
# container.clusters.get
# container.clusters.list
# container.clusters.getCredentials

##### setup bastion host service account to be attached to compute engine VM #####
resource "google_service_account" "service-account-bastion-host" {
  account_id   = "bastion-host-dev-account"
  display_name = "Dev Service Account for accessing Composer Environment through bastion host"
  description  = "Service account for dev purposes to access a private Composer Environment and run airflow/kubectl cli commands"
}

locals {
  bastion_service_account_roles = concat(var.bastion_service_account_roles_to_add, [
    "roles/composer.user",
    "roles/container.developer"
  ])
}

resource "google_project_iam_binding" "bastion-host-entry" {
  for_each = toset(local.bastion_service_account_roles)
  role     = each.value

  members = [
    "serviceAccount:${google_service_account.service-account-bastion-host.email}",
  ]
}

##### setup identity access proxy service account to be attached to be used by end user to ssh into compute engine VM #####
#TODO: build conditions for all the iam policy bindings to be specific to this custom setup
# download private key after terraform creates
resource "google_service_account" "service-account-iap-ssh" {
  account_id   = "service-account-iap-ssh"
  display_name = "A service account that can only ssh tunnel into the VM that then can access private IP composer"
  description  = "look at display name"
}

locals {
  ssh_service_account_roles = concat(var.ssh_service_account_roles_to_add, [
    "roles/iap.tunnelResourceAccessor",
    "roles/compute.viewer"
  ])
}

resource "google_project_iam_binding" "ssh-iap-compute-policy" {
  for_each = toset(local.ssh_service_account_roles)
  role     = each.value

  members = [
    "serviceAccount:${google_service_account.service-account-iap-ssh.email}",
  ]
}

##### setup service account to ensure composer environment is setup correctly #####
resource "google_service_account" "service-account-composer" {
  account_id   = "composer-dev-account"
  display_name = "Dev Service Account for Composer Environment"
  description  = "Service account for dev purposes to get a private Composer Environment running successfully"
}

resource "google_project_iam_member" "composer-worker" {
  role   = "roles/composer.worker"
  member = "serviceAccount:${google_service_account.service-account-composer.email}"
}