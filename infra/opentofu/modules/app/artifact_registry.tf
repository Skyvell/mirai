resource "google_artifact_registry_repository" "mirai" {
  location      = var.region
  repository_id = "mirai"
  format        = "DOCKER"
  labels        = local.labels

  depends_on = [google_project_service.required]
}
