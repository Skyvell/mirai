set positional-arguments := true

# List available recipes.
default:
    @just --list

# One-time per project: state bucket + Artifact Registry + APIs.
# Usage: just bootstrap-state <project> [region] [repo]
bootstrap-state project region="europe-north1" repo="mirai":
    ./scripts/bootstrap_state.sh {{project}} {{region}} {{repo}}

# One-time per project: WIF pool + CI service account for GitHub Actions deploys.
# Usage: just bootstrap-ci <project> <owner/repo> [region]
bootstrap-ci project github_repo region="europe-north1":
    ./scripts/bootstrap_ci.sh {{project}} {{github_repo}} {{region}}

# Initialize OpenTofu for the given environment.
tofu-init env:
    tofu -chdir=infra/opentofu/live init -backend-config=../config/{{env}}.gcs.tfbackend

# Plan changes for the given environment.
tofu-plan env: (tofu-init env)
    tofu -chdir=infra/opentofu/live plan -var-file=../config/{{env}}.tfvars

# Apply changes for the given environment. Extra args pass through
# (CI appends -auto-approve -var="image=..." to deploy a specific tag).
tofu-apply env *args: (tofu-init env)
    tofu -chdir=infra/opentofu/live apply -var-file=../config/{{env}}.tfvars {{args}}

# Destroy resources for the given environment.
tofu-destroy env: (tofu-init env)
    tofu -chdir=infra/opentofu/live destroy -var-file=../config/{{env}}.tfvars
