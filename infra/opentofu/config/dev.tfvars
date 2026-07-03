# Fill project_id. The Cloud Run image is CI-owned, not set here.
project_id = "mirai-dev-501218"
region     = "europe-north1"

db_tier                = "db-f1-micro"
db_deletion_protection = false # dev only; true in prod

clerk_jwks_url = "" # e.g. https://<slug>.clerk.accounts.dev/.well-known/jwks.json
