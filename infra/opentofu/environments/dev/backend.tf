terraform {
  backend "gcs" {
    bucket = "tofu-state-mirai-dev-501218"
    prefix = "app"
  }
}
