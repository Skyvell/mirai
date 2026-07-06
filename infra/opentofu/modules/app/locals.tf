# Module-wide labels applied to every resource that supports them.
locals {
  labels = {
    project = "mirai"
    managed = "opentofu"
  }

  # DB connection contract consumed by the backend (core/config.py) — one
  # source for both the Cloud Run service and the migration job.
  db_env = {
    INSTANCE_CONNECTION_NAME = google_sql_database_instance.main.connection_name
    DB_NAME                  = google_sql_database.app.name
    DB_IAM_USER              = google_sql_user.iam_sa.name
  }
}
