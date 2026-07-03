terraform {
  required_version = ">= 1.11"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    time = {
      source = "hashicorp/time"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
