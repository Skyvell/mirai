# Infrastructure — OpenTofu (GCP)

MVP infra for Mirai: **Cloud SQL (Postgres 17)** + **Cloud Run** (FastAPI). Two
run-once scripts bootstrap the state bucket + Artifact Registry + APIs and the
GitHub Actions trust; `just` wraps the OpenTofu commands. AWS→GCP translation of
the `xdata` reference layout. See `../../docs/stack.md` for scope.

```
live/        the deployable stack — database + api modules (only stateful tofu)
modules/     database (Cloud SQL), api (Cloud Run + IAM)
config/      dev.tfvars, dev.gcs.tfbackend
```

Bootstrap is two stateless scripts (`../../scripts/bootstrap_state.sh`,
`../../scripts/bootstrap_ci.sh`), not tofu stacks — create-once resources with
nothing to track. Commands run via the repo-root `justfile`. Auth: **IAM DB auth**
(no DB password); Cloud Run connects to Cloud SQL over the built-in connector
(public IP, no VPC); Clerk JWTs are verified in-app. CI authenticates to GCP with
**Workload Identity Federation** (keyless).

Run from the repo root.

## 1. Bootstrap (once per project)

```bash
just bootstrap-state <PROJECT>              # state bucket (tofu-state-<PROJECT>) + registry + APIs
just bootstrap-ci <PROJECT> <owner/repo>    # WIF + ci-deployer SA for GitHub Actions
```

Then fill `config/dev.gcs.tfbackend` (`bucket = tofu-state-<PROJECT>`) and
`config/dev.tfvars` (`project_id`, and `image` under the printed registry URL).

For CI, create a GitHub Environment `dev` and set the variables printed by
`bootstrap-ci`: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`,
`GCP_PROJECT_ID`, `GCP_REGION`. Push to `main` then runs `.github/workflows/deploy.yml`
(build+push image → `tofu apply`); steps 2–3 below are the manual equivalent.

## 2. Build & push the API image (normally CI does this)

CI builds and pushes on every push to `main`; run this by hand only to debug the
image or seed one before CI is wired.

```bash
gcloud auth configure-docker <REGION>-docker.pkg.dev
docker build -t <REGISTRY_URL>/mirai-api:<TAG> backend
docker push <REGISTRY_URL>/mirai-api:<TAG>
```

## 3. Deploy the live stack

```bash
just tofu-plan dev
just tofu-apply dev
```

Verify: `curl $(tofu -chdir=infra/opentofu/live output -raw api_url)/healthz` →
`{"status":"ok"}`; `/readyz` returns `200` once the IAM DB grant exists (see below).

## Notes

- **CI order:** `just bootstrap-state` + `just bootstrap-ci` (manual, once) →
  build+push image → `just tofu-apply`. On push to `main` the last two run in CI
  (image build via `docker/build-push-action` with GHA layer cache); the image is
  tagged with the commit SHA and passed to tofu via `-var="image=..."`.
- **IAM DB grants:** table-level `GRANT`s to the IAM DB role are not
  Terraform-manageable — run once as SQL (or fold into the first Alembic migration).
- **Private IP** is an additive change later (set `ipv4_enabled = false` +
  `private_network` on the instance, add `vpc_access` on Cloud Run) — see the TODO
  in `modules/database/cloudsql.tf`.
