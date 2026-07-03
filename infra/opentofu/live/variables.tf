variable "project_id" {
  type        = string
  description = "GCP project id to deploy into."
}

variable "region" {
  type        = string
  description = "Region for all resources."
  default     = "europe-north1"
}

variable "initial_image" {
  type        = string
  description = "Placeholder image at Cloud Run creation; the live image is owned by CI (ignore_changes)."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "db_tier" {
  type        = string
  description = "Cloud SQL machine tier."
  default     = "db-f1-micro"
}

variable "db_deletion_protection" {
  type        = bool
  description = "Block destroy of the Cloud SQL instance."
  default     = true
}

variable "clerk_jwks_url" {
  type        = string
  description = "Clerk public JWKS URL for JWT verification."
  default     = ""
}
