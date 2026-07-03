terraform {
  required_version = ">= 1.11"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.14"
    }
  }
}

provider "google" {
  project = "mirai-dev-501218"
  region  = "europe-north1"
}

module "app" {
  source = "../../modules/app"

  project_id             = "mirai-dev-501218"
  region                 = "europe-north1"
  db_tier                = "db-f1-micro"
  db_deletion_protection = false
}

output "api_url" {
  value       = module.app.api_url
  description = "Public URL of the Cloud Run API."
}

output "api_service_account" {
  value       = module.app.api_service_account
  description = "Runtime service account email."
}

output "database_connection_name" {
  value       = module.app.database_connection_name
  description = "project:region:instance — used by the Cloud SQL connector."
}
