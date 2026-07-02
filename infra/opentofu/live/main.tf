locals {
  labels = {
    project = "mirai"
    managed = "opentofu"
  }
}

# Runtime identity for the API. Lives at the root because it bridges the two
# modules: the database grants it IAM login, the api runs as it. Putting it in
# either module would create a database <-> api cycle.
resource "google_service_account" "api" {
  account_id   = "mirai-api-run"
  display_name = "Mirai API Cloud Run runtime"
}

resource "google_project_iam_member" "api_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_cloudsql_instance_user" {
  project = var.project_id
  role    = "roles/cloudsql.instanceUser"
  member  = "serviceAccount:${google_service_account.api.email}"
}

module "database" {
  source = "../modules/database"

  region              = var.region
  tier                = var.db_tier
  iam_user_email      = google_service_account.api.email
  deletion_protection = var.db_deletion_protection
  labels              = local.labels
}

module "api" {
  source = "../modules/api"

  project_id            = var.project_id
  region                = var.region
  image                 = var.image
  service_account_email = google_service_account.api.email

  cloudsql_connection_name = module.database.connection_name
  database_name            = module.database.database_name
  db_iam_user              = module.database.iam_user
  clerk_jwks_url           = var.clerk_jwks_url

  labels = local.labels
}
