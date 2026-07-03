# Cloud SQL provisions the IAM-auth role asynchronously after the instance is
# ready; wait so the user insert below doesn't race it.
resource "time_sleep" "iam_role_ready" {
  depends_on      = [google_sql_database_instance.main]
  create_duration = "60s"
}

# IAM DB login for the runtime SA — no password. Cloud SQL requires the user
# name to be the SA email with the ".gserviceaccount.com" suffix removed.
resource "google_sql_user" "iam_sa" {
  name       = trimsuffix(google_service_account.api.email, ".gserviceaccount.com")
  instance   = google_sql_database_instance.main.name
  type       = "CLOUD_IAM_SERVICE_ACCOUNT"
  depends_on = [time_sleep.iam_role_ready]
}
