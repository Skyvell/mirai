output "url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Public URL of the Cloud Run service."
}

output "service_name" {
  value = google_cloud_run_v2_service.api.name
}
