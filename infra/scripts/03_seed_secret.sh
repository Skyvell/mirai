#!/usr/bin/env bash
# Seed a Secret Manager secret with its real value. Run once per environment,
# after `tofu apply` (which creates the secret with a placeholder version).
# The value is prompted without echo (or piped via stdin) so it never appears
# in code, state, or shell history.
# Usage: 03_seed_secret.sh <project> [secret-id]
set -euo pipefail

project="${1:?project required}"
secret="${2:-anthropic-api-key}"

if [[ -t 0 ]]; then
    read -rs -p "Value for '$secret': " value
    echo >&2
else
    value="$(cat)"
fi
if [[ -z "$value" ]]; then
    echo "Empty value." >&2
    exit 1
fi

printf '%s' "$value" | gcloud secrets versions add "$secret" --data-file=- --project "$project"

echo "Done. New instances resolve 'latest' at start — the next deploy (or cold start) picks it up."
