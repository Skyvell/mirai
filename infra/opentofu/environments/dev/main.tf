module "app" {
  source = "../../modules/app"

  project_id             = "mirai-dev-501218"
  region                 = "europe-north1"
  db_tier                = "db-f1-micro"
  db_deletion_protection = false
  clerk_jwks_url         = "https://promoted-elephant-55.clerk.accounts.dev/.well-known/jwks.json"
  clerk_issuer           = "https://promoted-elephant-55.clerk.accounts.dev"
  frontend_origins       = "http://localhost:5173,https://mirai-web.pages.dev" # local dev + deployed Pages
}
