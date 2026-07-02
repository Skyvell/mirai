resource "google_cloud_run_v2_service" "api" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
  labels              = var.labels

  template {
    service_account = var.service_account_email

    scaling {
      max_instance_count = var.max_instances
    }

    # Built-in Cloud SQL connector — mounts the proxy socket under /cloudsql.
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [var.cloudsql_connection_name]
      }
    }

    containers {
      image = var.image

      resources {
        startup_cpu_boost = true
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name  = "INSTANCE_CONNECTION_NAME"
        value = var.cloudsql_connection_name
      }
      env {
        name  = "DB_NAME"
        value = var.database_name
      }
      env {
        name  = "DB_IAM_USER"
        value = var.db_iam_user
      }
      env {
        name  = "CLERK_JWKS_URL"
        value = var.clerk_jwks_url
      }

      startup_probe {
        http_get {
          path = "/healthz"
        }
      }
    }
  }
}

# Auth is enforced in-app via Clerk JWTs; Cloud Run itself is public.
resource "google_cloud_run_v2_service_iam_member" "public" {
  count = var.public_ingress ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
