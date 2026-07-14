module "app" {
  source = "../../modules/app"

  project_id             = "mirai-dev-501218"
  region                 = "europe-north1"
  db_tier                = "db-f1-micro"
  db_deletion_protection = false
  clerk_jwks_url         = "https://promoted-elephant-55.clerk.accounts.dev/.well-known/jwks.json"
  clerk_issuer           = "https://promoted-elephant-55.clerk.accounts.dev"
  frontend_origins       = "http://localhost:5173,https://mirai-web.pages.dev" # local dev + deployed Pages
  upload_allowlist       = "019f38f2-880d-7463-b5e4-9e976369aa08"              # ted; keeps the pre-settings gate
  bucket_force_destroy   = true

  # Set to the Cloud Run service URI after the first apply to enable async
  # parsing (self-URL cycle); until then parsing runs synchronously in-request.
  # worker_base_url = "https://mirai-api-xxxxxxxxxx.europe-north1.run.app"
}
