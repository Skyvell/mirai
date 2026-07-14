# Variables without defaults.
variable "project_id" {
  type        = string
  description = "GCP project id to deploy into."
}

variable "region" {
  type        = string
  description = "Region for all resources."
}

variable "tasks_location" {
  type        = string
  description = "Cloud Tasks queue location; must be a Cloud Tasks-supported region, which may differ from var.region. The queue dispatches to the worker over HTTPS, so cross-region is fine."
  default     = "europe-west1"
}

variable "image" {
  type        = string
  description = "Container image at Cloud Run creation only; the live image is CI-owned (ignore_changes)."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "clerk_jwks_url" {
  type        = string
  description = "Clerk public JWKS URL for JWT verification."
}

variable "clerk_issuer" {
  type        = string
  description = "Clerk issuer; the backend verifies token iss against it when set."
}

variable "frontend_origins" {
  type        = string
  description = "Comma-separated allow-list of origins permitted to call the API (CORS)."
}

variable "db_tier" {
  type        = string
  description = "Cloud SQL machine tier."
}

variable "db_deletion_protection" {
  type        = bool
  description = "Block destroy of the Cloud SQL instance."
}

# Variables with defaults.
variable "instance_name" {
  type        = string
  description = "Cloud SQL instance name."
  default     = "mirai"
}

variable "database_name" {
  type        = string
  description = "Application database created on the instance."
  default     = "mirai"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name."
  default     = "mirai-api"
}

variable "migration_job_name" {
  type        = string
  description = "Cloud Run job that applies database migrations."
  default     = "mirai-migrate"
}

variable "max_instances" {
  type        = number
  description = "Max Cloud Run instances. Min is 0 (scale to zero)."
  default     = 2
}

variable "upload_allowlist" {
  type        = string
  description = "Comma-separated user UUIDs allowed to upload lab PDFs (LLM cost gate). Empty allows all."
  default     = ""
}

variable "public_ingress" {
  type        = bool
  description = "Grant run.invoker to allUsers. Auth is enforced in-app via Clerk JWTs, not by Cloud Run."
  default     = true
}

variable "bucket_force_destroy" {
  type        = bool
  description = "Allow destroying the lab-uploads bucket even when it holds objects."
  default     = false
}

# The service's own URL can't be referenced from its own resource (cycle), so it
# is provided out-of-band: after the first apply, read the service URI and set
# this in the environment root, then re-apply. Non-empty enables async parsing.
variable "worker_base_url" {
  type        = string
  description = "This service's https base URL; the parse worker target and OIDC audience. Empty keeps parsing synchronous."
  default     = ""
}
