# Variables without defaults.
variable "project_id" {
  type        = string
  description = "GCP project id to deploy into."
}

variable "region" {
  type        = string
  description = "Region for all resources."
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

variable "max_instances" {
  type        = number
  description = "Max Cloud Run instances. Min is 0 (scale to zero)."
  default     = 2
}

variable "public_ingress" {
  type        = bool
  description = "Grant run.invoker to allUsers. Auth is enforced in-app via Clerk JWTs, not by Cloud Run."
  default     = true
}
