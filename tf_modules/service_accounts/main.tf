##### setup bastion host service account to be attached to compute engine VM #####
resource "google_service_account" "service-account-bastion-host" {
  project      = var.project
  account_id   = var.account_id_bastion_host
  display_name = var.display_name_bastion_host
  description  = var.description_bastion_host
}

# hard-coded as this is specific to cloud composer enablement
locals {
  bastion_service_account_roles = concat(var.bastion_service_account_roles_to_add, [
    "roles/composer.user",
    "roles/container.developer"
  ])
}

resource "google_project_iam_binding" "bastion-host-entry" {
  project  = var.project
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
  project      = var.project
  account_id   = var.account_id_iap_ssh
  display_name = var.display_name_iap_ssh
  description  = var.description_iap_ssh
}

# hard-coded as this is specific to identity aware proxy ssh enablement
locals {
  ssh_service_account_roles = concat(var.ssh_service_account_roles_to_add, [
    "roles/iap.tunnelResourceAccessor",
    "roles/compute.viewer"
  ])
}

resource "google_project_iam_binding" "ssh-iap-compute-policy" {
  project  = var.project
  for_each = toset(local.ssh_service_account_roles)
  role     = each.value

  members = [
    "serviceAccount:${google_service_account.service-account-iap-ssh.email}",
  ]
}

##### setup service account to ensure composer environment is setup correctly #####
resource "google_service_account" "service-account-composer" {
  project      = var.project
  account_id   = var.account_id_composer
  display_name = var.display_name_composer
  description  = var.description_composer
}

resource "google_project_iam_member" "composer-worker" {
  project = var.project
  role    = "roles/composer.worker" # hard-coded as this is specific to cloud composer enablement
  member  = "serviceAccount:${google_service_account.service-account-composer.email}"
}
