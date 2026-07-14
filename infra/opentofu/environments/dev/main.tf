module "app" {
  source = "../../modules/app"

  project_id             = "mirai-dev-501218"
  region                 = "europe-north1"
  tasks_location         = "europe-west1" # Cloud Tasks is not offered in europe-north1; queue dispatches cross-region.
  db_tier                = "db-f1-micro"
  db_deletion_protection = false
  clerk_jwks_url         = "https://promoted-elephant-55.clerk.accounts.dev/.well-known/jwks.json"
  clerk_issuer           = "https://promoted-elephant-55.clerk.accounts.dev"
  frontend_origins       = "http://localhost:5173,https://mirai-web.pages.dev"                         # local dev + deployed Pages
  upload_allowlist       = "019f38f2-880d-7463-b5e4-9e976369aa08,019f61fc-33bb-7664-a5f7-06058d7090bc" # ted + e2e test user
  bucket_force_destroy   = true
}
