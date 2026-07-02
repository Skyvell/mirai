output "api_url" {
  value       = module.api.url
  description = "Public URL of the Cloud Run API."
}

output "api_service_account" {
  value       = google_service_account.api.email
  description = "Runtime service account email."
}

output "database_connection_name" {
  value = module.database.connection_name
}
