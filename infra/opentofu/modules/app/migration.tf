# Database migrations run decoupled from serving: CI updates this job's image
# and executes it (alembic upgrade head) before each service deploy, so the API
# never runs DDL and a failed migration aborts the release.
resource "google_cloud_run_v2_job" "migrate" {
  name                = var.migration_job_name
  location            = var.region
  deletion_protection = false
  labels              = local.labels

  template {
    template {
      # TODO: run as a dedicated migrator SA (runtime SA drops to DML-only)
      # when health data lands — see docs/stack.md, Migrations.
      service_account = google_service_account.api.email

      # No /cloudsql volume: the backend reaches Cloud SQL via the Python
      # Connector, not the socket mount.
      containers {
        # Placeholder at creation only (never executed until CI sets a real
        # image); the live image is CI-owned, mirroring the service.
        image   = var.image
        command = ["alembic"]
        args    = ["upgrade", "head"]

        dynamic "env" {
          for_each = local.db_env
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  # gcloud run jobs update stamps client metadata, like deploy-cloudrun does
  # for the service.
  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}
