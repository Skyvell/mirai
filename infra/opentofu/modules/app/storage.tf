# Bucket for user-uploaded files. Objects are namespaced per user and domain,
# e.g. users/{user_id}/labs/{upload_id}.pdf, so account deletion is one prefix
# delete and new domains get sibling prefixes.
resource "google_storage_bucket" "user_uploads" {
  name                        = "${var.project_id}-user-uploads"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.bucket_force_destroy
  labels                      = local.labels

  depends_on = [google_project_service.required]
}

# Runtime SA reads and writes user objects. objectUser (not objectAdmin): with
# uniform bucket-level access the extra ACL/IAM-admin permissions are dead weight.
resource "google_storage_bucket_iam_member" "api_object_user" {
  bucket = google_storage_bucket.user_uploads.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.api.email}"
}
