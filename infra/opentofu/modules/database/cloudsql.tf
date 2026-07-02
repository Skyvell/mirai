resource "google_sql_database_instance" "main" {
  name             = var.instance_name
  region           = var.region
  database_version = "POSTGRES_17"

  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    availability_type = "ZONAL"
    user_labels       = var.labels

    # Public IP + built-in Cloud SQL connector. No authorized networks: access
    # is IAM-only over Google's network. TODO: swap to private IP (ipv4_enabled
    # = false + private_network) when health-data compliance requires it.
    ip_configuration {
      ipv4_enabled = true
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled = true
    }
  }
}
