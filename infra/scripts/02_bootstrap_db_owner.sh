#!/usr/bin/env bash
# Make the runtime SA's IAM DB user own the app database. Idempotent, run once per environment.
# Chicken-and-egg: requires a superuser session inside Postgres, which OpenTofu doesn't have.
# Ownership (via pg_database_owner on PG 15+) covers all future Alembic DDL — no per-table grants.
# Requires psql and cloud-sql-proxy on PATH; authenticates with Application Default Credentials.
# Usage: 02_bootstrap_db_owner.sh <project> [instance] [database]
set -euo pipefail

project="${1:?project required}"
instance="${2:-mirai}"
database="${3:-mirai}"
port=5433

export CLOUDSDK_CORE_PROJECT="$project"

# Read the IAM DB user tofu created (users.tf) from the live instance instead
# of duplicating the SA name and Cloud SQL's username-derivation rule here.
db_user="$(gcloud sql users list --instance "$instance" \
    --filter "type=CLOUD_IAM_SERVICE_ACCOUNT" --format "value(name)")"
if [[ -z "$db_user" || "$db_user" == *$'\n'* ]]; then
    echo "Expected exactly one IAM service-account DB user on '$instance', got: '${db_user:-none}'" >&2
    exit 1
fi

echo ">> Setting a throwaway password on the built-in postgres user..."
password="$(openssl rand -base64 24)"
gcloud sql users set-password postgres --instance "$instance" --password "$password"

connection_name="$(gcloud sql instances describe "$instance" --format 'value(connectionName)')"

echo ">> Starting Cloud SQL proxy for $connection_name..."
cloud-sql-proxy "$connection_name" --port "$port" &
proxy_pid=$!
trap 'kill "$proxy_pid"' EXIT
for _ in $(seq 1 20); do
    pg_isready -h 127.0.0.1 -p "$port" -q && break
    sleep 0.5
done

echo ">> Transferring ownership of database '$database' to '$db_user'..."
# postgres must be a member of a role to hand it ownership; membership is revoked after.
PGPASSWORD="$password" psql -h 127.0.0.1 -p "$port" -U postgres -d postgres \
    -v ON_ERROR_STOP=1 <<SQL
GRANT "${db_user}" TO postgres;
ALTER DATABASE ${database} OWNER TO "${db_user}";
REVOKE "${db_user}" FROM postgres;
SQL

echo
echo "Done. '$db_user' owns '$database'; migrations (alembic upgrade head) can now run DDL."
