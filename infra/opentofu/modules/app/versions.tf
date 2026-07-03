# The module declares which providers it needs; version constraints and the
# lock file live at the root stack that calls it.
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    time = {
      source = "hashicorp/time"
    }
  }
}
