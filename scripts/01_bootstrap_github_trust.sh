#!/usr/bin/env bash
# Keyless GitHub Actions -> GCP trust (WIF pool + provider + ci-deployer SA). Idempotent.
# Create-if-absent only: config changes to the pool/provider/SA are not reapplied on re-run.
# Usage: 01_bootstrap_github_trust.sh <project> <github_repo> [region]
set -euo pipefail

project="${1:?project required}"
github_repo="${2:?github_repo required}"
region="${3:-europe-north1}"

pool="github-pool"
provider="github"
sa_name="ci-deployer"
sa_email="${sa_name}@${project}.iam.gserviceaccount.com"
bucket="tofu-state-${project}"

project_number="$(gcloud projects describe "$project" --format='value(projectNumber)')"

# Broad deployer so this script stays generic across projects/stacks. Tighten to
# a custom, resource-scoped role for prod.
ci_roles=(
    roles/editor
    roles/resourcemanager.projectIamAdmin
)

echo ">> Enabling trust/IAM APIs (idempotent)..."
gcloud services enable \
    serviceusage.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    sts.googleapis.com \
    storage.googleapis.com \
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
    --member "serviceAccount:${sa_email}" --role roles/storage.objectAdmin >/dev/null

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
