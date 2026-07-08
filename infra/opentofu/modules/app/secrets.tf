# Anthropic API key for lab-PDF parsing. Tofu owns the secret shape only; the
# value is seeded manually once per project (never in code or state):
#   echo -n "sk-ant-..." | gcloud secrets versions add anthropic-api-key --data-file=-
resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  labels    = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

# Read access scoped to this secret only, not project-wide.
resource "google_secret_manager_secret_iam_member" "api_anthropic_key_accessor" {
  secret_id = google_secret_manager_secret.anthropic_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}
