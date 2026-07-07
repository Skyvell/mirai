# Runtime identity for the API: the database grants it IAM login, Cloud Run runs as it.
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

# Calls Claude on Vertex AI to parse lab PDFs (keyless, via ADC).
resource "google_project_iam_member" "api_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}
