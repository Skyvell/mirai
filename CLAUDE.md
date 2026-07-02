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
- `backend/` — FastAPI on Cloud Run (uv). **Scaffold only:** settings, Cloud SQL engine, Clerk JWT auth dep, health endpoints. No domain models yet.
- `infra/` — GCP infrastructure (OpenTofu). Cloud SQL + Cloud Run for MVP.
- Planned per `stack.md`: Cloud Storage for uploaded lab files, biomarker data model. `[LATER]`: DuckLake lakehouse + SQLMesh once omics/wearable scale demands it.

## Frontend

Run from `frontend/` (package manager **pnpm**):

```bash
pnpm dev      # Vite dev server (http://localhost:5173); regenerates the route tree
pnpm build    # tsc -b (typecheck) then vite build
pnpm lint     # oxlint
```

Stack: Vite 8 + React 19 + TypeScript, TanStack Router, Tailwind v4, shadcn/ui (Radix + lucide-react, Geist font).

**Current state.** Six routes scaffolded as placeholder pages: `/` (Overview), `/biomarkers`, `/physiology`, `/omics`, `/insights`, `/interventions`. Nav lives in `__root.tsx`. Routes cover the full product vision; only biomarkers is in MVP scope.

**Routing — TanStack Router, file-based.** A file under `src/routes/` becomes a URL (`index.tsx`→`/`, `about.tsx`→`/about`). The Vite plugin regenerates `src/routeTree.gen.ts` on dev/build — **never edit it by hand.** `src/routes/__root.tsx` is the shared layout (nav + `<Outlet/>`); `src/main.tsx` builds and mounts the router.

**Styling — Tailwind v4 + shadcn tokens.** `src/index.css` holds `@import "tailwindcss"` plus tokens. Real colors live in `:root` / `.dark` (`--background`, `--primary`, …); the `@theme inline` block maps them to Tailwind's color namespace so `bg-background`/`text-primary` work and dark-mode overrides resolve live. **Re-theme by editing `:root`/`.dark` values, not the `@theme` mapping.**

**shadcn/ui.** Components land in `src/components/ui/` via `pnpm dlx shadcn@latest add <name>`. `cn()` in `src/lib/utils.ts` merges class strings. The `@/*` → `src/*` alias is declared in both `vite.config.ts` and the tsconfigs (duplication is intentional: bundler vs. typechecker/shadcn CLI).

## Backend

Run from `backend/` (package manager **uv**):

```bash
uv sync                                   # resolve deps + venv
uv run uvicorn mirai_api.main:app --reload
```

src-layout single package `mirai_api` (`src/mirai_api/`): `main.py` (app + CORS), `core/` (`config` settings, `db` Cloud SQL engine, `security` Clerk JWT verify, `deps` FastAPI dependencies), `routers/` (`health` → `/healthz`, `/readyz`). Scaffold only — add domain models/routers per MVP scope.

**Cloud SQL:** SQLAlchemy engine via the Cloud SQL Python Connector with **IAM DB auth** (no password) in `core/db.py`. Same code path for public-IP-now and private-IP-later.

**Clerk:** JWTs verified against the public JWKS (`core/security.py`); no secret key needed for verification. `Dockerfile` builds with `uv sync --frozen`, runs non-root, serves on `$PORT`.

## Infrastructure

`infra/opentofu/` — OpenTofu on GCP, layout mirrors the `xdata` reference (`live/ + modules/ + config/`; see `infra/opentofu/README.md`). Bootstrap is two stateless scripts: `scripts/bootstrap_state.sh` (`just bootstrap-state <project>`) provisions state bucket (`tofu-state-<project>`) + Artifact Registry + API enablement; `scripts/bootstrap_ci.sh` (`just bootstrap-ci <project> <owner/repo>`) provisions the Workload Identity Federation pool + `ci-deployer` SA for GitHub Actions. `live/` is the only stateful stack — composes `database` (Cloud SQL Postgres 17, IAM auth) + `api` (Cloud Run v2), state in GCS. Commands run through the repo-root `justfile` (`just tofu-plan/apply <env>`). Cloud Run reaches Cloud SQL via the built-in connector (public IP, no VPC); private IP is an additive change later. The runtime SA lives in `live/main.tf` (bridges both modules — avoids a cycle).

**CI/CD** — `.github/workflows/deploy.yml` runs on push to `main`: `_deploy-image.yml` (build + push `mirai-api:<sha>` to Artifact Registry) → `_deploy-infrastructure.yml` (`just tofu-apply dev` with the SHA image threaded via `-var`). Keyless GCP auth via WIF; GitHub Environment `dev` holds `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`.

## Deferred frontend wiring

Not yet wired in `frontend/`: Clerk auth (`@clerk/clerk-react`), TanStack Query, and the `@hey-api/openapi-ts` API client generated from the backend's OpenAPI schema (the backend now exposes one).

## Commits

- Short and concise.
- No mention of Claude / AI authorship (no `Co-Authored-By`, no generated-with footer).

## Writing
Concise without losing vital context. Scientific report style writing. Zero fluff tolerated.
