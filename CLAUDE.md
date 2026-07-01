# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Mirai** — a direct-to-consumer precision-health app for individuals optimizing their own health. MVP scope is **blood biomarkers only**; wearables and omics come later. D2C, not HIPAA-regulated yet (see `docs/`).

## Repo layout

- `docs/` — **stack decisions** (the source of truth for tech choices): `description.md` (product), `stack.md` (frontend + backend stack, tagged `[MVP]`/`[LATER]`).
- `frontend/` — the web app (built). Everything below lives here.
- Backend — **not built yet.** Planned: FastAPI + Pydantic v2, SQLAlchemy 2.0 async, on Cloud Run, with Cloud SQL for Postgres and Clerk auth.

## Frontend

Run all commands from `frontend/` (package manager is **pnpm**):

```bash
pnpm dev      # Vite dev server (http://localhost:5173); also regenerates the route tree
pnpm build    # tsc -b (typecheck) then vite build
pnpm lint     # oxlint
```

Stack: Vite 8 + React 19 + TS, TanStack Router, Tailwind v4, shadcn/ui.

**Routing — TanStack Router, file-based.** Add a file under `src/routes/` and the filename becomes the URL (`index.tsx`→`/`, `about.tsx`→`/about`). The Vite plugin regenerates `src/routeTree.gen.ts` on dev/build — **never edit it by hand.** `src/routes/__root.tsx` is the shared layout (nav + `<Outlet/>`). `src/main.tsx` builds the router and mounts it.

**Styling — Tailwind v4 + shadcn tokens.** `src/index.css` holds `@import "tailwindcss"` plus the design tokens. The real colors live in `:root` / `.dark` as `--background`, `--primary`, etc.; the `@theme inline` block maps them to Tailwind's color namespace so `bg-background`/`text-primary` work and dark-mode overrides resolve live. **To re-theme the whole app, edit the `:root`/`.dark` values — not the `@theme` mapping.**

**shadcn/ui.** Components land in `src/components/ui/` (`pnpm dlx shadcn@latest add <name>`). `cn()` in `src/lib/utils.ts` merges class strings. The `@/*` import alias → `src/*` is configured in both `vite.config.ts` and the tsconfigs (the duplication is intentional: bundler vs. typechecker/shadcn CLI).

## Commits

- Short and concise.
- No mention of Claude / AI authorship (no `Co-Authored-By`, no generated-with footer).

## Writing
Concise without losing vital context. Scientific report style writing. Zero fluff tolerated.

## Not yet wired (deliberately deferred until the backend exists)

Clerk auth (`@clerk/clerk-react`), TanStack Query, and the `@hey-api/openapi-ts` API client generated from the FastAPI OpenAPI schema.
