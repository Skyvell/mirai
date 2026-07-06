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
      service_account = google_service_account.api.email

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.main.connection_name]
        }
      }

      containers {
        # Placeholder at creation only (never executed until CI sets a real
        # image); the live image is CI-owned, mirroring the service.
        image   = var.image
        command = ["alembic"]
        args    = ["upgrade", "head"]

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }

        env {
          name  = "INSTANCE_CONNECTION_NAME"
          value = google_sql_database_instance.main.connection_name
        }
        env {
          name  = "DB_NAME"
          value = google_sql_database.app.name
        }
        env {
          name  = "DB_IAM_USER"
          value = google_sql_user.iam_sa.name
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
