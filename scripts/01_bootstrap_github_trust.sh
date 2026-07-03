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
pool_resource="projects/${project_number}/locations/global/workloadIdentityPools/${pool}"

# Broad, generic deployer — one role covers any stack. Scope down for prod.
ci_roles=(
    roles/owner
)

export CLOUDSDK_CORE_PROJECT="$project"

echo ">> Enabling APIs for IAM, Workload Identity, and token exchange..."
gcloud services enable \
    serviceusage.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    sts.googleapis.com \
    storage.googleapis.com

echo ">> Ensuring Workload Identity pool '$pool' exists (holds external identities)..."
if ! gcloud iam workload-identity-pools describe "$pool" --location global >/dev/null 2>&1; then
    gcloud iam workload-identity-pools create "$pool" --location global \
        --display-name "GitHub Actions"
fi

echo ">> Ensuring OIDC provider '$provider' trusts GitHub repo '$github_repo'..."
if ! gcloud iam workload-identity-pools providers describe "$provider" \
    --location global --workload-identity-pool "$pool" >/dev/null 2>&1; then
    gcloud iam workload-identity-pools providers create-oidc "$provider" \
        --location global --workload-identity-pool "$pool" \
        --display-name "GitHub" \
        --issuer-uri "https://token.actions.githubusercontent.com" \
        --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
        --attribute-condition "assertion.repository == '${github_repo}'"
fi

echo ">> Ensuring CI deploy service account '$sa_name' exists..."
if ! gcloud iam service-accounts describe "$sa_email" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$sa_name" --display-name "GitHub Actions CI deployer"
fi

echo ">> Granting the deployer permission to run OpenTofu and deploy..."
for role in "${ci_roles[@]}"; do
    gcloud projects add-iam-policy-binding "$project" \
        --member "serviceAccount:${sa_email}" --role "$role" \
        --condition None --quiet >/dev/null
done

echo ">> Granting the deployer read/write on the tofu state bucket (gs://$bucket)..."
gcloud storage buckets add-iam-policy-binding "gs://$bucket" \
    --member "serviceAccount:${sa_email}" --role roles/storage.objectAdmin >/dev/null

echo ">> Allowing GitHub Actions in '$github_repo' to impersonate the deployer..."
gcloud iam service-accounts add-iam-policy-binding "$sa_email" \
    --member "principalSet://iam.googleapis.com/${pool_resource}/attribute.repository/${github_repo}" \
    --role roles/iam.workloadIdentityUser >/dev/null

echo
echo "Done. Set these as GitHub Environment 'dev' variables:"
echo "  GCP_WORKLOAD_IDENTITY_PROVIDER = ${pool_resource}/providers/${provider}"
echo "  GCP_SERVICE_ACCOUNT            = ${sa_email}"
echo "  GCP_PROJECT_ID                 = ${project}"
echo "  GCP_REGION                     = ${region}"
