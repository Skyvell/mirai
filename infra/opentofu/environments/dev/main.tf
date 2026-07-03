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
  clerk_jwks_url         = "" # no Clerk in dev
}

output "api_url" {
  value = module.app.api_url
}

output "api_service_account" {
  value = module.app.api_service_account
}

output "database_connection_name" {
  value = module.app.database_connection_name
}
