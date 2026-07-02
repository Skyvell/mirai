resource "google_sql_database" "app" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
}
