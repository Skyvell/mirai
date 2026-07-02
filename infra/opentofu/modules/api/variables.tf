variable "project_id" {
  type        = string
  description = "GCP project id."
}

variable "region" {
  type        = string
  description = "Region for the Cloud Run service."
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name."
  default     = "mirai-api"
}

variable "image" {
  type        = string
  description = "Full container image reference (Artifact Registry URL + tag)."
}

variable "service_account_email" {
  type        = string
  description = "Runtime service account the service runs as (created at the root)."
}

variable "cloudsql_connection_name" {
  type        = string
  description = "Cloud SQL connection name (project:region:instance) to attach."
}

variable "database_name" {
  type        = string
  description = "Application database name, passed to the app as DB_NAME."
}

variable "db_iam_user" {
  type        = string
  description = "IAM DB login name, passed to the app as DB_IAM_USER."
}

variable "clerk_jwks_url" {
  type        = string
  description = "Clerk public JWKS URL for JWT verification."
  default     = ""
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

variable "labels" {
  type        = map(string)
  description = "Labels applied to the service."
  default     = {}
}
