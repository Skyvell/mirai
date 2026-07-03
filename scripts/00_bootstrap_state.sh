#!/usr/bin/env bash
# Create the OpenTofu state bucket. Idempotent.
# Enables only the APIs needed to make the bucket; app APIs are OpenTofu's.
# Usage: 00_bootstrap_state.sh <project> [region]
set -euo pipefail

project="${1:?project required}"
region="${2:-europe-north1}"
bucket="tofu-state-${project}"

echo ">> Enabling state APIs (idempotent)..."
gcloud services enable \
    serviceusage.googleapis.com \
    storage.googleapis.com \
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

echo
echo "Done. config/dev.gcs.tfbackend -> bucket = \"$bucket\""
