output "api_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "Public URL of the Cloud Run API."
}

output "user_uploads_bucket" {
  value       = google_storage_bucket.user_uploads.name
  description = "Bucket holding user-uploaded files."
}

output "database_connection_name" {
  value       = google_sql_database_instance.main.connection_name
  description = "project:region:instance — used by the Cloud SQL connector."
}
