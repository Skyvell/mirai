# Read back the project number for the deterministic Cloud Run URL below.
data "google_project" "this" {}

# Module-wide labels applied to every resource that supports them.
locals {
  labels = {
    project = "mirai"
    managed = "opentofu"
  }

  # The service's own Cloud Run URL, computed from the deterministic
  # {service}-{project_number}.{region}.run.app format rather than read back
  # from the service resource — that would be a self-reference cycle. This is
  # the parse worker target and its OIDC audience; a single apply wires it.
  worker_base_url = "https://${var.service_name}-${data.google_project.this.number}.${var.region}.run.app"

  # DB connection contract consumed by the backend (core/config.py) — one
  # source for both the Cloud Run service and the migration job.
  db_env = {
    INSTANCE_CONNECTION_NAME = google_sql_database_instance.main.connection_name
    DB_NAME                  = google_sql_database.app.name
    DB_IAM_USER              = google_sql_user.iam_sa.name
  }
}
