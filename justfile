set positional-arguments := true

# List available recipes.
default:
    @just --list

# Bootstrap the OpenTofu state bucket.
bootstrap-state project region="europe-north1":
    ./infra/scripts/00_bootstrap_state.sh {{project}} {{region}}

# Bootstrap GitHub -> GCP trust (WIF + ci-deployer SA).
bootstrap-trust project github_repo region="europe-north1":
    ./infra/scripts/01_bootstrap_github_trust.sh {{project}} {{github_repo}} {{region}}

# Initialize OpenTofu for the given environment.
tofu-init env:
    tofu -chdir=infra/opentofu/environments/{{env}} init

# Plan changes for the given environment.
tofu-plan env: (tofu-init env)
    tofu -chdir=infra/opentofu/environments/{{env}} plan

# Apply changes for the given environment (CI appends -auto-approve).
tofu-apply env *args: (tofu-init env)
    tofu -chdir=infra/opentofu/environments/{{env}} apply {{args}}

# Destroy resources for the given environment.
tofu-destroy env: (tofu-init env)
    tofu -chdir=infra/opentofu/environments/{{env}} destroy
