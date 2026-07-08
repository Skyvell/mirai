# Anthropic API key for lab-PDF parsing. Tofu owns the secret shape and a
# placeholder version; the real value is seeded once per project via
# `just seed-secret <project>` and never enters code or state.
resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key"
  labels    = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

# Placeholder first version so the Cloud Run revision (which references
# "latest") can start before the real key exists. Seeding adds version 2 and
# "latest" resolves to it on the next instance start.
resource "google_secret_manager_secret_version" "anthropic_api_key_placeholder" {
  secret      = google_secret_manager_secret.anthropic_api_key.id
  secret_data = "placeholder-seed-real-key"
}

# Read access scoped to this secret only, not project-wide.
resource "google_secret_manager_secret_iam_member" "api_anthropic_key_accessor" {
  secret_id = google_secret_manager_secret.anthropic_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}
