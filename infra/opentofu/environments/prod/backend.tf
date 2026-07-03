terraform {
  backend "gcs" {
    bucket = "tofu-state-REPLACE_ME" # prod project's state bucket (created by bootstrap-state)
    prefix = "app"
  }
}
