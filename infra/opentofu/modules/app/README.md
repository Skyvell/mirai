# Module: app

The whole Mirai app stack as one composable unit. An environment root
(`environments/<env>`) sets the provider + backend and calls this module with
env-specific values (`project_id`, `region`, `db_tier`, `db_deletion_protection`).

Provisions:

- **APIs** (`apis.tf`) — `google_project_service` for run, artifactregistry, sqladmin.
- **Artifact Registry** (`artifact_registry.tf`) — Docker repo for the backend image.
- **Cloud SQL** (`cloudsql.tf`, `users.tf`) — Postgres 17, IAM auth, runtime-SA DB user.
- **IAM** (`iam.tf`) — runtime service account + its Cloud SQL roles.
- **Cloud Run** (`cloud_run.tf`) — the API service, public invoker, `/cloudsql` connector.
- **Migration job** (`migration.tf`) — `mirai-migrate`, same runtime SA and DB wiring
  as the service; runs `alembic upgrade head`, executed by CI before each release.

**Image contract:** the Cloud Run service and migration job are created with a
placeholder `image` and `ignore_changes` on the container image. Terraform owns
the *shape*; GitHub Actions owns the running *image* (`deploy-cloudrun` for the
service, `gcloud run jobs update` for the job). So a `tofu apply` never reverts
the deployed revision.

**DB ownership contract:** the runtime SA's IAM DB user must own the app
database for migrations to run DDL — granted once per environment by
`infra/scripts/02_bootstrap_db_owner.sh` (superuser-only SQL, outside tofu).
