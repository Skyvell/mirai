# Backend

## MVP

**API**
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 (async) + Alembic migrations
- uv
- Ruff
- Cloud Run


**Database**
- One Postgres as system of record — **Neon** (serverless, scale-to-zero, ~free idle)
- Cloud Storage (GCS) only once users upload lab files

**Auth**
- **Clerk** — verify the JWT in a FastAPI dependency; store only `clerk_user_id`. No health data in Clerk.

## Deferred (add only when needed)
- Lakehouse (DuckLake / BigQuery / Iceberg) — when omics or dense wearable data create analytical scale
- Cloud Run Jobs — batch ingestion (lab PDF/CSV parsing)
- Cloud SQL / AlloyDB — drop-in Postgres upgrade if Neon is outgrown

## Revisit if HIPAA applies (lab-test ordering, provider relationships — much later)
- Auth → GCP Identity Platform (self-serve BAA; Clerk's BAA is Enterprise-only)
- Sign BAAs for DB + storage; consider Cloud Healthcare API (FHIR) + Sensitive Data Protection
