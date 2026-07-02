# Fill project_id and image (image = <bootstrap registry_url>/mirai-api:<tag>).
project_id = "REPLACE_ME"
region     = "europe-north1"
image      = "europe-north1-docker.pkg.dev/REPLACE_ME/mirai/mirai-api:latest"

db_tier                = "db-f1-micro"
db_deletion_protection = false # dev only; true in prod

clerk_jwks_url = "" # e.g. https://<slug>.clerk.accounts.dev/.well-known/jwks.json
