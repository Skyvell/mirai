# Scaffold — not applied yet. Before first apply: create the prod GCP project,
# run `just bootstrap-state`/`bootstrap-trust` for it, fill the values below +
# backend.tf, set the prod GitHub Environment vars, and add a prod deploy job.

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
  project = "REPLACE_ME"
  region  = "europe-north1"
}

module "app" {
  source = "../../modules/app"

  project_id             = "REPLACE_ME"
  region                 = "europe-north1"
  db_tier                = "db-f1-micro" # bump for prod load
  db_deletion_protection = true
  clerk_jwks_url         = "" # prod Clerk JWKS URL
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
