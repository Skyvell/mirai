resource "google_project_service" "required" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    # "secretmanager.googleapis.com", # add when a secret exists
    # "compute.googleapis.com",       # add for private IP later
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
