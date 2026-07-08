resource "google_cloud_run_v2_service" "api" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
  labels              = local.labels

  # The env block references the secret by id only, so tofu can't see that the
  # revision needs a version of it to start — order explicitly.
  depends_on = [google_secret_manager_secret_version.anthropic_api_key_placeholder]

  template {
    service_account = google_service_account.api.email

    scaling {
      max_instance_count = var.max_instances
    }

    # Built-in Cloud SQL connector — mounts the proxy socket under /cloudsql.
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
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

      dynamic "env" {
        for_each = local.db_env
        content {
          name  = env.key
          value = env.value
        }
      }
      env {
        name  = "CLERK_JWKS_URL"
        value = var.clerk_jwks_url
      }
      env {
        name  = "CLERK_ISSUER"
        value = var.clerk_issuer
      }
      env {
        name  = "FRONTEND_ORIGINS"
        value = var.frontend_origins
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.user_uploads.name
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.anthropic_api_key.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/healthz"
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # CI (deploy-cloudrun) owns the running image; tofu owns the service shape.
  # deploy-cloudrun also stamps client metadata and template labels — ignored
  # so a plan after a release stays clean.
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].labels,
      client,
      client_version,
    ]
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
