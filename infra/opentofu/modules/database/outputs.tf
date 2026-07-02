output "connection_name" {
  value       = google_sql_database_instance.main.connection_name
  description = "project:region:instance — used by the Cloud SQL connector."
}

output "instance_name" {
  value = google_sql_database_instance.main.name
}

output "database_name" {
  value = google_sql_database.app.name
}

output "iam_user" {
  value       = google_sql_user.iam_sa.name
  description = "IAM DB login name (SA email, suffix stripped)."
}
