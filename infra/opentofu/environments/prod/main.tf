# Scaffold — not applied yet. Before first apply: create the prod GCP project,
# run `just bootstrap-state`/`bootstrap-trust` for it, fill the values here +
# providers.tf + backend.tf, set the prod GitHub Environment vars, and add a
# prod deploy job.

module "app" {
  source = "../../modules/app"

  project_id             = "REPLACE_ME"
  region                 = "europe-north1"
  db_tier                = "db-f1-micro" # bump for prod load
  db_deletion_protection = true
  clerk_jwks_url         = "" # prod Clerk JWKS URL
  clerk_issuer           = "" # prod Clerk issuer
  frontend_origins       = "" # prod frontend origin(s), comma-separated, e.g. https://app.example.com
}
