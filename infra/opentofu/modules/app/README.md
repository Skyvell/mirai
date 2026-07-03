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

**Image contract:** Cloud Run is created with a placeholder `image` and
`ignore_changes` on the container image. Terraform owns the service *shape*;
GitHub Actions owns the running *image* (via `deploy-cloudrun`). So a `tofu apply`
never reverts the deployed revision.
