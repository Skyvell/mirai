#!/usr/bin/env bash
# One-time per project: set up keyless auth for GitHub Actions deploys.
# Creates a Workload Identity pool + OIDC provider trusting one GitHub repo, a
# CI deployer service account, and the IAM grants tofu needs to manage the
# stack. Idempotent — safe to re-run.
#
# Separate from bootstrap_state.sh on purpose: the state substrate is needed for
# any deploy (including local), while CI trust is opt-in, needs the repo name,
# and carries a broad IAM grant worth isolating.
#
# Usage: bootstrap_ci.sh <project> <github_repo> [region]
#   github_repo: "owner/name" (e.g. Skyvell/mirai)
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <project> <github_repo> [region]" >&2
    echo "  github_repo: owner/name (e.g. Skyvell/mirai)" >&2
    exit 1
fi

project="$1"
github_repo="$2"
region="${3:-europe-north1}"

pool="github-pool"
provider="github"
sa_name="ci-deployer"
sa_email="${sa_name}@${project}.iam.gserviceaccount.com"
bucket="tofu-state-${project}"

project_number="$(gcloud projects describe "$project" --format='value(projectNumber)')"

# CI runs tofu, which creates the runtime SA and grants it project roles, builds
# and pushes images, and manages Cloud Run + Cloud SQL. projectIamAdmin is broad
# — acceptable for a single dev project; tighten to a custom role when prod lands.
ci_roles=(
    roles/run.admin
    roles/artifactregistry.writer
    roles/cloudsql.admin
    roles/iam.serviceAccountAdmin
    roles/iam.serviceAccountUser
    roles/resourcemanager.projectIamAdmin
    roles/serviceusage.serviceUsageConsumer
)

echo ">> Enabling APIs (idempotent)..."
gcloud services enable \
    iamcredentials.googleapis.com \
    sts.googleapis.com \
    --project "$project"

echo ">> Workload Identity pool $pool ..."
if ! gcloud iam workload-identity-pools describe "$pool" \
    --project "$project" --location global >/dev/null 2>&1; then
    gcloud iam workload-identity-pools create "$pool" \
        --project "$project" --location global \
        --display-name "GitHub Actions"
fi

echo ">> OIDC provider $provider (trusts repo $github_repo) ..."
if ! gcloud iam workload-identity-pools providers describe "$provider" \
    --project "$project" --location global --workload-identity-pool "$pool" >/dev/null 2>&1; then
    gcloud iam workload-identity-pools providers create-oidc "$provider" \
        --project "$project" --location global --workload-identity-pool "$pool" \
        --display-name "GitHub" \
        --issuer-uri "https://token.actions.githubusercontent.com" \
        --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
        --attribute-condition "assertion.repository == '${github_repo}'"
fi

echo ">> CI service account $sa_email ..."
if ! gcloud iam service-accounts describe "$sa_email" --project "$project" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$sa_name" \
        --project "$project" --display-name "GitHub Actions CI deployer"
fi

echo ">> Project role grants ..."
for role in "${ci_roles[@]}"; do
    gcloud projects add-iam-policy-binding "$project" \
        --member "serviceAccount:${sa_email}" --role "$role" \
        --condition None --quiet >/dev/null
done

echo ">> State bucket access (gs://$bucket) ..."
gcloud storage buckets add-iam-policy-binding "gs://$bucket" \
    --member "serviceAccount:${sa_email}" --role roles/storage.admin >/dev/null

echo ">> Letting the repo impersonate $sa_name via WIF ..."
principal="principalSet://iam.googleapis.com/projects/${project_number}/locations/global/workloadIdentityPools/${pool}/attribute.repository/${github_repo}"
gcloud iam service-accounts add-iam-policy-binding "$sa_email" \
    --project "$project" \
    --member "$principal" --role roles/iam.workloadIdentityUser >/dev/null

provider_resource="projects/${project_number}/locations/global/workloadIdentityPools/${pool}/providers/${provider}"

echo
echo "Done. Set these as GitHub Environment 'dev' variables:"
echo "  GCP_WORKLOAD_IDENTITY_PROVIDER = ${provider_resource}"
echo "  GCP_SERVICE_ACCOUNT            = ${sa_email}"
echo "  GCP_PROJECT_ID                 = ${project}"
echo "  GCP_REGION                     = ${region}"
