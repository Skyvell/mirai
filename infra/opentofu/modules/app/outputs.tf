output "api_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Public URL of the Cloud Run API."
}

output "api_service_account" {
  value       = google_service_account.api.email
  description = "Runtime service account email."
}

output "database_connection_name" {
  value       = google_sql_database_instance.main.connection_name
  description = "project:region:instance — used by the Cloud SQL connector."
}
