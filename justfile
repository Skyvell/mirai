set positional-arguments := true

# List available recipes.
default:
    @just --list

# One-time per project: state bucket + Artifact Registry + APIs.
# Usage: just bootstrap <project> [region] [repo]
bootstrap project region="europe-north1" repo="mirai":
    ./scripts/bootstrap.sh {{project}} {{region}} {{repo}}

# Initialize OpenTofu for the given environment.
tofu-init env:
    tofu -chdir=infra/opentofu/live init -backend-config=../config/{{env}}.gcs.tfbackend

# Plan changes for the given environment.
tofu-plan env: (tofu-init env)
    tofu -chdir=infra/opentofu/live plan -var-file=../config/{{env}}.tfvars

# Apply changes for the given environment.
tofu-apply env: (tofu-init env)
    tofu -chdir=infra/opentofu/live apply -var-file=../config/{{env}}.tfvars

# Destroy resources for the given environment.
tofu-destroy env: (tofu-init env)
    tofu -chdir=infra/opentofu/live destroy -var-file=../config/{{env}}.tfvars

# Build and push the backend image. Usage: just build-push <registry-url> <tag>
build-push registry tag:
    docker build -t {{registry}}/mirai-api:{{tag}} backend
    docker push {{registry}}/mirai-api:{{tag}}
