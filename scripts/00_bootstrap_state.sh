#!/usr/bin/env bash
# Create the OpenTofu state bucket. Idempotent.
# Enables only the APIs needed to make the bucket; app APIs are OpenTofu's.
# Usage: 00_bootstrap_state.sh <project> [region]
set -euo pipefail

project="${1:?project required}"
region="${2:-europe-north1}"
bucket="tofu-state-${project}"

export CLOUDSDK_CORE_PROJECT="$project"

echo ">> Enabling APIs for storage and service management..."
gcloud services enable \
    serviceusage.googleapis.com \
    storage.googleapis.com

echo ">> Ensuring the tofu state bucket exists (gs://$bucket)..."
if ! gcloud storage buckets describe "gs://$bucket" >/dev/null 2>&1; then
    gcloud storage buckets create "gs://$bucket" \
        --location "$region" \
        --uniform-bucket-level-access \
        --public-access-prevention
fi
gcloud storage buckets update "gs://$bucket" --versioning

echo
echo "Done. config/dev.gcs.tfbackend -> bucket = \"$bucket\""
