# Infrastructure — OpenTofu (GCP)

MVP infra for Mirai: **Cloud SQL (Postgres 17)** + **Cloud Run** (FastAPI). A
run-once script bootstraps the state bucket, Artifact Registry, and API
enablement; `just` wraps the OpenTofu commands. AWS→GCP translation of the
`xdata` reference layout. See `../../docs/stack.md` for scope.

```
live/        the deployable stack — database + api modules (only stateful tofu)
modules/     database (Cloud SQL), api (Cloud Run + IAM)
config/      dev.tfvars, dev.gcs.tfbackend
```

Bootstrap is a stateless script (`../../scripts/bootstrap.sh`), not a tofu stack —
create-once resources with nothing to track. Commands run via the repo-root
`justfile`. Auth: **IAM DB auth** (no DB password); Cloud Run connects to Cloud SQL
over the built-in connector (public IP, no VPC); Clerk JWTs are verified in-app.

Run from the repo root.

## 1. Bootstrap (once per project)

```bash
just bootstrap <PROJECT>          # state bucket (tofu-state-<PROJECT>) + registry + APIs
```

Then fill `config/dev.gcs.tfbackend` (`bucket = tofu-state-<PROJECT>`) and
`config/dev.tfvars` (`project_id`, and `image` under the printed registry URL).

## 2. Build & push the API image

```bash
gcloud auth configure-docker <REGION>-docker.pkg.dev
just build-push <REGISTRY_URL> <TAG>
```

## 3. Deploy the live stack

```bash
just tofu-plan dev
just tofu-apply dev
```

Verify: `curl $(tofu -chdir=infra/opentofu/live output -raw api_url)/healthz` →
`{"status":"ok"}`; `/readyz` returns `200` once the IAM DB grant exists (see below).

## Notes

- **CI order:** `just bootstrap` (manual, once) → `just build-push` → `just tofu-apply`.
- **IAM DB grants:** table-level `GRANT`s to the IAM DB role are not
  Terraform-manageable — run once as SQL (or fold into the first Alembic migration).
- **Private IP** is an additive change later (set `ipv4_enabled = false` +
  `private_network` on the instance, add `vpc_access` on Cloud Run) — see the TODO
  in `modules/database/cloudsql.tf`.
