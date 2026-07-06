# The module declares its providers with minimum versions; the ~> upper pin
# and the lock file live at the root stack that calls it.
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.14"
    }
  }
}
