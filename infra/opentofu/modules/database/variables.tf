variable "region" {
  type        = string
  description = "Region for the Cloud SQL instance."
}

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

variable "tier" {
  type        = string
  description = "Cloud SQL machine tier."
  default     = "db-f1-micro"
}

variable "iam_user_email" {
  type        = string
  description = "Runtime service account email granted IAM DB login. The module strips the .gserviceaccount.com suffix as Cloud SQL requires."
}

variable "deletion_protection" {
  type        = bool
  description = "Block destroy of the instance."
  default     = true
}

variable "labels" {
  type        = map(string)
  description = "Labels applied to the instance."
  default     = {}
}
