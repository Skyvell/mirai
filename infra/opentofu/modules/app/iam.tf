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

# Enqueue parse tasks onto the Cloud Tasks queue.
resource "google_project_iam_member" "api_cloudtasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Act as itself, so Cloud Tasks can mint worker OIDC tokens under this identity
# (reuse the runtime SA as the invoker for MVP; a dedicated invoker is [LATER]).
resource "google_service_account_iam_member" "api_acts_as_self" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.api.email}"
}
