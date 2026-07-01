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

- `frontend/` — the web app. Built. Everything below concerns it.
- Backend — **not built.** Planned per `stack.md`: FastAPI on Cloud Run, Cloud SQL for Postgres (operational data), Cloud Storage for uploaded lab files, Clerk auth (Clerk `user_id` linked to own user table; no health data in Clerk). `[LATER]`: DuckLake lakehouse + SQLMesh once omics/wearable scale demands it.

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

## Deferred until the backend exists

Clerk auth (`@clerk/clerk-react`), TanStack Query, and the `@hey-api/openapi-ts` API client generated from the FastAPI OpenAPI schema. Not yet wired.

## Commits

- Short and concise.
- No mention of Claude / AI authorship (no `Co-Authored-By`, no generated-with footer).

## Writing
Concise without losing vital context. Scientific report style writing. Zero fluff tolerated.
