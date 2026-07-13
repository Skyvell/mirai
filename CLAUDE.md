# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## Product

**Mirai** — a direct-to-consumer precision-health app: individuals understand, track, and optimize their own biology from their own data. The loop is Measure → Interpret → Personalize → Intervene → Evaluate → Adjust.

**MVP scope is blood biomarkers only** (users upload lab PDFs; biomarkers tracked over time). Physiology (Oura/wearables), omics, interventions, and AI recommendations are product vision, not MVP. Not positioned as a medical device.

## Source of truth

`docs/` holds the decisions; code follows it, not the reverse.

- `docs/description.md` — product, personalization loop, full data model, long-term vision.
- `docs/stack.md` — frontend + backend stack, every choice tagged `[MVP]` (needed to ship) or `[LATER]` (add when a stated trigger hits). Consult before adding a dependency; respect the tags.

## Repo layout

Polyglot monorepo — each concern is a top-level sibling owning its own toolchain (no shared root package manager). Kept in one repo because the frontend generates its API client from the backend's OpenAPI schema (an atomic contract) and infra deploys the backend image. **Split trigger:** extract `infra/` into its own repo only when someone else owns infrastructure, or health-data compliance requires prod infra/state/secrets under separate access.

- `frontend/` — the web app (pnpm). Built.
- `backend/` — FastAPI on Cloud Run (uv). Settings, Cloud SQL engine, Clerk JWT auth, health endpoints, and the first domain feature: lab-PDF upload → GCS → LLM parse → biomarker tables.
- `infra/` — GCP infrastructure (OpenTofu). Cloud SQL + Cloud Run + a user-uploads GCS bucket + Secret Manager (Anthropic API key), for MVP.
- `[LATER]` per `stack.md`: DuckLake lakehouse + SQLMesh once omics/wearable scale demands it; direct lab/FHIR integration.

## Frontend

Run from `frontend/` (package manager **pnpm**):

```bash
pnpm dev      # Vite dev server (http://localhost:5173); regenerates the route tree
pnpm build    # tsc -b (typecheck) then vite build
pnpm lint     # oxlint
```

Stack: Vite 8 + React 19 + TypeScript, TanStack Router, TanStack Query, Tailwind v4, shadcn/ui (Radix + lucide-react, Geist font), generated API client (`@hey-api/openapi-ts`).

**Current state.** Six routes scaffolded as placeholder pages: `/` (Overview), `/biomarkers`, `/physiology`, `/omics`, `/insights`, `/interventions`. Nav lives in `__root.tsx`. Routes cover the full product vision; only biomarkers is in MVP scope.

**Routing — TanStack Router, file-based.** A file under `src/routes/` becomes a URL (`index.tsx`→`/`, `about.tsx`→`/about`). The Vite plugin regenerates `src/routeTree.gen.ts` on dev/build — **never edit it by hand.** `src/routes/__root.tsx` is the shared layout (nav + `<Outlet/>`); `src/main.tsx` builds and mounts the router.

**Styling — Tailwind v4 + shadcn tokens.** `src/index.css` holds `@import "tailwindcss"` plus tokens. Real colors live in `:root` / `.dark` (`--background`, `--primary`, …); the `@theme inline` block maps them to Tailwind's color namespace so `bg-background`/`text-primary` work and dark-mode overrides resolve live. **Re-theme by editing `:root`/`.dark` values, not the `@theme` mapping.**

**shadcn/ui.** Components land in `src/components/ui/` via `pnpm dlx shadcn@latest add <name>`. `cn()` in `src/lib/utils.ts` merges class strings. The `@/*` → `src/*` alias is declared in both `vite.config.ts` and the tsconfigs (duplication is intentional: bundler vs. typechecker/shadcn CLI).

## Backend

Run from `backend/` (package manager **uv**):

```bash
uv sync                                   # resolve deps + venv
uv run uvicorn mirai_api.main:app --reload
uv run pytest                             # router tests use fakes; no DB or network
uv run ruff check && uv run ruff format   # lint + format (config in pyproject.toml)
```

src-layout single package `mirai_api` (`src/mirai_api/`), layered with domain-named files: `main.py` (app assembly + lifespan: logging config, engine warm-up), `core/` (`config` settings, `db` Cloud SQL engine, `security` Clerk JWT verify, `deps` FastAPI dependencies incl. service providers, `enums` shared vocabulary like `UploadStatus`), `models/` (SQLAlchemy, one file per model; `base.py` holds `Base` with the Alembic naming convention; `__init__.py` aggregates), `schemas/` (Pydantic API models, one module per router), `routers/` (`health`, `me`, `biomarkers`, `lab_uploads`), `services/` (`biomarkers` `BiomarkerService`, `storage` GCS client, `lab_parsing` Pydantic AI agent + pure `map_extraction`, `lab_uploads` persistence), `repositories/` (`biomarkers` `BiomarkerRepository`). New domain feature = model + schema + router + service + repository (thin layers where logic is trivial). Revisit module-per-domain packages when a second real domain (physiology) lands.

**Biomarker domain — endpoint → service → repository.** Routers stay thin (validate, resolve `CurrentUser`, delegate, map domain errors to `HTTPException`); `BiomarkerService` owns application logic and the transaction boundary (one commit per mutating method, bulk all-or-nothing); `BiomarkerRepository` owns DB access (flushes, never commits; plain ORM returns; queries scope by `user_id`). Service mutations take the subject `user_id` — the seam for future lab/admin actors (authorize actor-vs-subject in the service later; no roles now). Endpoints: `GET /biomarkers` (catalogue), `GET /biomarker-series[/{slug}]` (per-user time series), `POST|PATCH|DELETE /biomarker-measurements` (bulk; DELETE takes `ids` query params). Ownership failures return 404 identical to nonexistent ids (no existence leak). All measurement writes — manual and lab-parse — go through `BiomarkerRepository.add_measurements`.

**Lab PDF upload → biomarkers.** `POST /lab-uploads` (multipart, Clerk-authed) stores the PDF in GCS (`users/{user_id}/labs/{upload_id}.pdf`), then Claude (`claude-opus-4-8` via the Anthropic API, through Pydantic AI) parses it into `biomarker_measurements` mapped against the seeded `biomarkers` catalogue (`slug` is the LLM key; `loinc_code`+UCUM `canonical_unit` for future FHIR). Parsing is synchronous in-request; blocking GCS/DB work runs via `run_in_threadpool` (no async SQLAlchemy). Extra settings: `GCS_BUCKET`, `GCP_PROJECT_ID` (keyless via ADC), `ANTHROPIC_API_KEY` (Secret Manager on Cloud Run; `backend/.env` locally), and `UPLOAD_ALLOWLIST` (comma-separated user UUIDs allowed to upload — LLM cost gate; empty allows all; set per env in tofu). Units stored verbatim; canonical conversion is `[LATER]`.

**Cloud SQL:** SQLAlchemy engine via the Cloud SQL Python Connector with **IAM DB auth** (no password) in `core/db.py`. Same code path for public-IP-now and private-IP-later.

**Migrations — Alembic**, configured via `[tool.alembic]` in `pyproject.toml` (no `alembic.ini`); `alembic/env.py` reuses the app engine. Models are the schema source of truth: new table/column = model change + `uv run alembic revision --autogenerate -m "..."` + review. Applied by the `mirai-migrate` Cloud Run job, which CI executes before each service deploy — the API never runs DDL. Primary keys are client-generated UUIDv7 (`uuid.uuid7`, Python 3.14).

**Users — JIT provisioning.** No Clerk webhook: on the first authenticated request, `get_current_user` (`core/deps.py`) upserts a `users` row keyed on the Clerk `sub` (race-safe `ON CONFLICT DO NOTHING`) and returns the ORM `User`. Clerk webhook is `[LATER]` per `docs/stack.md` (trigger: deletion cleanup once health data lands).

**Clerk:** JWTs verified against the public JWKS (`core/security.py`); no secret key needed for verification. `Dockerfile` builds with `uv sync --frozen`, copies `alembic/` (one image serves API + migration job), runs non-root, serves on `$PORT`.

## Infrastructure

`infra/opentofu/` — OpenTofu on GCP (`environments/<env>/ + modules/app/`; see `infra/opentofu/README.md`). **Two planes.** Bootstrap is three stateless scripts creating only what tofu can't: `infra/scripts/00_bootstrap_state.sh` (`just bootstrap-state <project>`) → state bucket (`tofu-state-<project>`); `infra/scripts/01_bootstrap_github_trust.sh` (`just bootstrap-trust <project> <owner/repo>`) → WIF pool + `ci-deployer` SA; `infra/scripts/02_bootstrap_db_owner.sh` (`just bootstrap-db <project>`, after first apply) → runtime SA owns the app database (superuser-only SQL; ownership covers all future DDL). OpenTofu owns everything declarative, all in a single `modules/app` module — APIs (`google_project_service`, incl. `storage` + `secretmanager`), Artifact Registry, runtime SA + IAM (`cloudsql.client`/`instanceUser`, `storage.objectUser` on the uploads bucket, `secretmanager.secretAccessor` on the API-key secret), Cloud SQL (Postgres 17, IAM auth), a `<project>-user-uploads` GCS bucket (`storage.tf`), the `anthropic-api-key` secret (`secrets.tf` — shape + placeholder version; the real value never enters code/state), Cloud Run v2 (service + `mirai-migrate` migration job). **Manual step (not tofu-able):** seed the real Anthropic API key once per project after the first apply — `just seed-secret <project>` (prompts for the key); parsing fails until seeded. Each `environments/<env>/` is a self-contained root (its own `backend.tf` + inlined values in `main.tf`) that calls `modules/app` — one env per GCP project; state in GCS. `dev` is live, `prod` is a scaffold. The Cloud Run service and migration job are created with a placeholder image + `ignore_changes` on the image, so CI owns the running revision and tofu owns the shape. Cloud Run→Cloud SQL via built-in connector (public IP); private IP is additive later.

**CI/CD** — `.github/workflows/deploy.yml` on push to `main`: `_deploy-infrastructure.yml` (`just tofu-apply dev`) → `_deploy-app.yml` (build/push `mirai-api:<sha>`, execute the `mirai-migrate` job with the new image, then `deploy-cloudrun@v3` updating only the service image), plus `_deploy-frontend.yml` (build + `wrangler pages deploy` to Cloudflare Pages) running independently. Keyless GCP auth via WIF; GitHub Environment `dev` holds `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`, plus `CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` for the frontend.

## Frontend wiring

**Clerk auth — wired.** `@clerk/react` (v6). `ClerkProvider` wraps the router in `main.tsx` (key from `VITE_CLERK_PUBLISHABLE_KEY`); `__root.tsx` gates the whole app — `<Show when="signed-in">` renders nav + `<UserButton/>`, `signed-out` renders `<SignIn/>`. Overview (`routes/index.tsx`) fetches the protected backend `GET /me` via the generated client to confirm the token verifies. Build config (`VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY`) lives in the committed `frontend/.env` — both values are public, not secrets; a gitignored `.env.local` overrides it for a local backend (`.env.local` > `.env`).

**Frontend hosting — Cloudflare Pages (Direct Upload).** The frontend is a static Vite SPA, deployed from CI via `_deploy-frontend.yml` (build with pnpm, upload `dist/` with `npx wrangler pages deploy`). Deliberately **not** the Cloudflare GitHub App: that would grant a third party write access to this auto-deploying repo. Instead CI holds a Cloudflare API token scoped to Pages (`CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` in the `dev` Environment) — Cloudflare gets no repo access. Build config comes from the committed `frontend/.env`. `public/_redirects` (`/* /index.html 200`) serves the SPA catch-all so client-side deep links don't 404. Backend CORS is an allow-list (`frontend_origins`, comma-separated) covering both `localhost:5173` and the Pages origin.

**API client — generated (`@hey-api/openapi-ts` + TanStack Query).** `pnpm generate:api` dumps the backend's OpenAPI schema (`backend/scripts/export_openapi.py` — importing the app has no side effects, no env needed) and regenerates `src/client/` (fetch client, typed SDK, `*Options()`/`*Mutation()` TanStack Query helpers keyed on the backend's `operation_id`s). Run it whenever the backend contract changes; `src/client/` is committed (CI's frontend job is pnpm-only), the intermediate `openapi.json` is gitignored. The client configures itself at creation via hey-api's `runtimeConfigPath` → `createClientConfig` in `src/lib/api.ts` (`baseUrl` from `VITE_API_URL`, Clerk token via hey-api's `auth` — attached only to operations the spec marks Bearer-secured, `HTTPBearer` in `core/deps.py`); `ApiProvider` in `main.tsx` (inside `ClerkProvider`) just injects Clerk's render-scoped `getToken`. `QueryClientProvider` wraps the router; queries refetch only on explicit invalidation (`staleTime` 5 min, no focus refetch). Routes consume `currentUserOptions`, `listBiomarkersOptions`, `uploadLabMutation` (upload invalidates `listBiomarkersQueryKey` on success); `apiErrorMessage` surfaces FastAPI's `detail` from thrown error bodies.

## Commits
- Short and concise.
- No mention of Claude / AI authorship (no `Co-Authored-By`, no generated-with footer).

## Writing
Concise without losing vital context. Scientific report style writing. Zero fluff tolerated.

## Code
- Best coding practises.
- Comments start wich capital letter and ends with period.
- Use the latest versions unless they are unstable.
- Multi-step function bodies: blank line between logical steps, one intent comment leading each step. No comments on trivial one-expression bodies; no trailing per-line comments.
