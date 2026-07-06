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

`infra/opentofu/` — OpenTofu on GCP (`environments/<env>/ + modules/app/`; see `infra/opentofu/README.md`). **Two planes.** Bootstrap is two stateless scripts creating only the chicken-and-egg foundation: `infra/scripts/00_bootstrap_state.sh` (`just bootstrap-state <project>`) → state bucket (`tofu-state-<project>`); `infra/scripts/01_bootstrap_github_trust.sh` (`just bootstrap-trust <project> <owner/repo>`) → WIF pool + `ci-deployer` SA. OpenTofu owns everything declarative, all in a single `modules/app` module — APIs (`google_project_service`), Artifact Registry, runtime SA + IAM, Cloud SQL (Postgres 17, IAM auth), Cloud Run v2. Each `environments/<env>/` is a self-contained root (its own `backend.tf` + inlined values in `main.tf`) that calls `modules/app` — one env per GCP project; state in GCS. `dev` is live, `prod` is a scaffold. Cloud Run is created with a placeholder image + `ignore_changes` on the image, so CI owns the running revision and tofu owns the shape. Cloud Run→Cloud SQL via built-in connector (public IP); private IP is additive later.

**CI/CD** — `.github/workflows/deploy.yml` on push to `main`: `_deploy-infrastructure.yml` (`just tofu-apply dev`) → `_deploy-app.yml` (build/push `mirai-api:<sha>`, then `deploy-cloudrun@v3` updating only the image), plus `_deploy-frontend.yml` (build + `wrangler pages deploy` to Cloudflare Pages) running independently. Keyless GCP auth via WIF; GitHub Environment `dev` holds `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`, plus `CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` for the frontend.

## Frontend wiring

**Clerk auth — wired.** `@clerk/react` (v6). `ClerkProvider` wraps the router in `main.tsx` (key from `VITE_CLERK_PUBLISHABLE_KEY`); `__root.tsx` gates the whole app — `<Show when="signed-in">` renders nav + `<UserButton/>`, `signed-out` renders `<SignIn/>`. Overview (`routes/index.tsx`) fetches the protected backend `GET /me` via `useAuth().getToken()` (`src/lib/api.ts`) to confirm the token verifies. Build config (`VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY`) lives in the committed `frontend/.env` — both values are public, not secrets; a gitignored `.env.local` overrides it for a local backend (`.env.local` > `.env`).

**Frontend hosting — Cloudflare Pages (Direct Upload).** The frontend is a static Vite SPA, deployed from CI via `_deploy-frontend.yml` (build with pnpm, upload `dist/` with `npx wrangler pages deploy`). Deliberately **not** the Cloudflare GitHub App: that would grant a third party write access to this auto-deploying repo. Instead CI holds a Cloudflare API token scoped to Pages (`CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` in the `dev` Environment) — Cloudflare gets no repo access. Build config comes from the committed `frontend/.env`. `public/_redirects` (`/* /index.html 200`) serves the SPA catch-all so client-side deep links don't 404. Backend CORS is an allow-list (`frontend_origins`, comma-separated) covering both `localhost:5173` and the Pages origin.

**Still deferred:** TanStack Query, and the `@hey-api/openapi-ts` API client generated from the backend's OpenAPI schema.

## Commits
- Short and concise.
- No mention of Claude / AI authorship (no `Co-Authored-By`, no generated-with footer).

## Writing
Concise without losing vital context. Scientific report style writing. Zero fluff tolerated.

## Code
- Best coding practises.
- Comments start wich capital letter and ends with period.
- Use the latest versions unless they are unstable.
