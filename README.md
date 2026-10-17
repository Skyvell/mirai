# Mirai

Direct-to-consumer precision-health app.

## Project structure

- `docs/` — product spec and stack decisions (source of truth).
- `CLAUDE.md` — architecture, commands, and conventions for this repo.
- `frontend/` — the web app.
- `api/` — FastAPI API.
- `infra/` — GCP infrastructure (OpenTofu).

## Local development

Requires [pnpm](https://pnpm.io), [uv](https://docs.astral.sh/uv), and `gcloud`. The local API uses the dev cloud resources (Cloud SQL, GCS) via ADC; local config lives in the untracked `api/.env`.

One-time setup:

```bash
gcloud auth application-default login \
  --impersonate-service-account=mirai-api-run@mirai-dev-501218.iam.gserviceaccount.com
cd api && uv sync
cd frontend && pnpm install
```

The loop — API and frontend in separate terminals:

```bash
cd api && uv run uvicorn mirai_api.main:app --reload   # http://localhost:8000
cd frontend && pnpm dev                                # http://localhost:5173
```

### Frontend

`frontend/.env.local` points the app at the local API. After changing the API contract:

```bash
pnpm generate:api
```

Before committing:

```bash
pnpm build && pnpm lint
```

### API

Tests, lint, and format before committing:

```bash
uv run pytest
uv run ruff check && uv run ruff format
```

Schema changes: edit the SQLAlchemy model, then generate and review a migration. CI applies migrations on deploy (the `mirai-migrate` job); the API never runs DDL.

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

### Docs

The ER diagram (`docs/architecture/data_models/er_diagram.d2`) is maintained by hand; update it in the same change as any model change, then re-render the SVG. Requires [D2](https://d2lang.com) (`brew install d2`).

```bash
just generate-er-diagram
```
