# Infrastructure — OpenTofu (GCP)

MVP infra for Mirai: **Cloud SQL (Postgres 17)** + **Cloud Run** (FastAPI).

```
environments/<env>/  per-env root — backend + provider + inlined values, calls the module
modules/app/         the whole app: APIs, registry, IAM, Cloud SQL, Cloud Run
```

Each environment is its own root with a fully-declared backend (its project's
state bucket) and values inlined in `main.tf` — one env per GCP project. `dev` is
live; `prod` is a scaffold (fill its placeholders + bootstrap its project before
applying).

**Two planes.** Bootstrap (bash, once) creates only the chicken-and-egg
foundation — the state bucket and the GitHub↔GCP trust. OpenTofu owns everything
declarative: APIs, Artifact Registry, Cloud SQL, IAM, and the
Cloud Run **service shape**. GitHub Actions owns **releases**: build → push →
`deploy-cloudrun` updates only the image. tofu creates Cloud Run with a
placeholder image and `ignore_changes` on it, so the two never fight.

Auth: **IAM DB auth** (no DB password); Cloud Run reaches Cloud SQL over the
built-in connector (public IP); Clerk JWTs verified in-app; CI is keyless via
**Workload Identity Federation**. Run from the repo root.

Clerk + CORS are configured per-env via `modules/app` variables (`clerk_jwks_url`,
`clerk_issuer`, `frontend_origins`), all set in each `environments/<env>/main.tf`.
`frontend_origins` is a comma-separated CORS allow-list (local dev origin + the
deployed frontend origin). The values are public (JWKS URL, issuer, allowed
origins), not secrets.

The one real secret — the Anthropic API key for lab-PDF parsing — lives in
**Secret Manager** (`modules/app/secrets.tf`): tofu owns the secret shape and
the runtime SA's per-secret accessor grant; the value is seeded manually once
per project (see Setup) and never enters code or state.

**Async lab parsing** (`modules/app/tasks.tf`): a Cloud Tasks queue the API
enqueues onto; Cloud Tasks calls the internal parse worker back with an OIDC
token minted as the runtime SA (`iam.tf`). Because the worker's target is the
service's own URL — a reference cycle tofu can't resolve — `worker_base_url` is
provided out-of-band: after the first apply, read the `api_url` output and set
`worker_base_url` in `environments/<env>/main.tf`, then re-apply. It stays
synchronous (parsing in-request) until that value is set.

## Setup (once per project)

Bootstrap creates the foundation tofu can't manage itself — the state bucket and
the keyless GitHub↔GCP trust. Both are idempotent; run once from the repo root:

```bash
just bootstrap-state <PROJECT>                 # OpenTofu state bucket
just bootstrap-trust <PROJECT> <owner/repo>    # WIF pool + ci-deployer SA
just bootstrap-db <PROJECT>                    # runtime SA owns the app database (after first apply)
```

After the first `tofu apply`, seed the real Anthropic API key (tofu creates the
secret with a placeholder version so Cloud Run starts; lab parsing fails until
the real key is added — new instances pick up `latest` on start):

```bash
just seed-secret <PROJECT>    # prompts for the key (anthropic-api-key by default)
```

`bootstrap-db` runs after the first `tofu apply` (the instance and IAM DB user
must exist). It transfers ownership of the app database to the runtime SA's IAM
DB user — a superuser-only SQL statement tofu can't issue — so Alembic
migrations can run DDL. Ownership covers all future tables; no per-table grants.

Then set the `project_id`/`region`/backend `bucket` in `environments/<env>/`
(`main.tf` + `backend.tf`), and set the four `dev` GitHub Environment variables
printed by `bootstrap-trust` (`GCP_WORKLOAD_IDENTITY_PROVIDER`,
`GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`). Push to `main` →
`deploy.yml` applies infra then releases the app.

## Local

```bash
just tofu-plan dev      # needs: gcloud auth application-default login
just tofu-apply dev
```

Verify: `curl $(tofu -chdir=infra/opentofu/environments/dev output -raw api_url)/readyz` →
`{"status":"ready"}`.

## Notes

- **Migrations:** the `mirai-migrate` Cloud Run job (`modules/app/migration.tf`)
  applies Alembic migrations; CI updates its image and executes it before each
  service deploy. Like the service, tofu owns its shape and CI owns its image.
- **Release drift:** after the first release, `just tofu-plan dev` should be clean.
  If it churns a `run.googleapis.com/client-name` annotation, add that path to the
  Cloud Run `ignore_changes`.
- **CI privilege:** the `ci-deployer` SA holds `roles/owner` — fine for an
  isolated dev project; scope to a custom role for prod.
- **Private IP** is an additive change later — see the TODO in `modules/app/cloudsql.tf`.
