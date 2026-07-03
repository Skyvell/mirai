# Infrastructure — OpenTofu (GCP)

MVP infra for Mirai: **Cloud SQL (Postgres 17)** + **Cloud Run** (FastAPI).

```
live/        the deployable stack — APIs, registry, database + api modules
modules/     database (Cloud SQL), api (Cloud Run + IAM)
config/      dev.tfvars, dev.gcs.tfbackend
```

**Two planes.** Bootstrap (bash, once) creates only the chicken-and-egg
foundation — the state bucket and the GitHub↔GCP trust. OpenTofu owns everything
declarative: APIs, Artifact Registry, Cloud SQL, IAM, and the
Cloud Run **service shape**. GitHub Actions owns **releases**: build → push →
`deploy-cloudrun` updates only the image. tofu creates Cloud Run with a
placeholder image and `ignore_changes` on it, so the two never fight.

Auth: **IAM DB auth** (no DB password); Cloud Run reaches Cloud SQL over the
built-in connector (public IP); Clerk JWTs verified in-app; CI is keyless via
**Workload Identity Federation**. Run from the repo root.

## Setup (once per project)

Bootstrap creates the foundation tofu can't manage itself — the state bucket and
the keyless GitHub↔GCP trust. Both are idempotent; run once from the repo root:

```bash
just bootstrap-state <PROJECT>                 # OpenTofu state bucket
just bootstrap-trust <PROJECT> <owner/repo>    # WIF pool + ci-deployer SA
```

Then fill `config/dev.gcs.tfbackend` (`bucket = tofu-state-<PROJECT>`) and
`config/dev.tfvars` (`project_id`), and set the four `dev` GitHub Environment
variables printed by `bootstrap-trust` (`GCP_WORKLOAD_IDENTITY_PROVIDER`,
`GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`). Push to `main` →
`deploy.yml` applies infra then releases the app.

## Local

```bash
just tofu-plan dev      # needs: gcloud auth application-default login
just tofu-apply dev
```

Verify: `curl $(tofu -chdir=infra/opentofu/live output -raw api_url)/healthz` →
`{"status":"ok"}`.

## Notes

- **IAM DB grants:** table-level `GRANT`s to the IAM DB role aren't
  Terraform-manageable — run once as SQL (or fold into the first Alembic migration).
- **Release drift:** after the first release, `just tofu-plan dev` should be clean.
  If it churns a `run.googleapis.com/client-name` annotation, add that path to the
  Cloud Run `ignore_changes`.
- **CI privilege:** the `ci-deployer` SA holds `roles/editor` + `projectIamAdmin`
  (near-owner) — fine for an isolated dev project; scope to a custom role for prod.
- **Private IP** is an additive change later — see the TODO in `modules/database/cloudsql.tf`.
