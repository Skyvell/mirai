# IAM DB login for the runtime SA — no password. Cloud SQL requires the user
# name to be the SA email with the ".gserviceaccount.com" suffix removed.
resource "google_sql_user" "iam_sa" {
  name     = trimsuffix(var.iam_user_email, ".gserviceaccount.com")
  instance = google_sql_database_instance.main.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}
