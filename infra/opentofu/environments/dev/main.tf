module "app" {
  source = "../../modules/app"

  project_id             = "mirai-dev-501218"
  region                 = "europe-north1"
  db_tier                = "db-f1-micro"
  db_deletion_protection = false
  clerk_jwks_url         = "" # no Clerk in dev
}
