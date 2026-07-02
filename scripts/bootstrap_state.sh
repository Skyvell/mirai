#!/usr/bin/env bash
# One-time per project: create the OpenTofu state bucket + Artifact Registry repo
# and enable the required GCP APIs. Idempotent — safe to re-run.
#
# The state bucket is derived from the project id (tofu-state-<project>). GCP
# project ids are globally unique, so this needs no separate uniqueness token —
# the analog of xdata deriving its bucket from the AWS account id.
#
# Usage: bootstrap.sh <project> [region] [repo]
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <project> [region] [repo]" >&2
    exit 1
fi

project="$1"
region="${2:-europe-north1}"
repo="${3:-mirai}"
bucket="tofu-state-${project}"

echo ">> Enabling APIs (idempotent)..."
gcloud services enable \
    storage.googleapis.com \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    iam.googleapis.com \
    compute.googleapis.com \
    --project "$project"

echo ">> State bucket gs://$bucket ..."
if ! gcloud storage buckets describe "gs://$bucket" --project "$project" >/dev/null 2>&1; then
    gcloud storage buckets create "gs://$bucket" \
        --project "$project" \
        --location "$region" \
        --uniform-bucket-level-access \
        --public-access-prevention
fi
gcloud storage buckets update "gs://$bucket" --versioning

echo ">> Artifact Registry $repo ..."
if ! gcloud artifacts repositories describe "$repo" \
    --project "$project" --location "$region" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$repo" \
        --project "$project" --location "$region" --repository-format docker
fi

echo
echo "Done."
echo "  config/dev.gcs.tfbackend -> bucket = \"$bucket\""
echo "  registry URL             -> ${region}-docker.pkg.dev/${project}/${repo}"
