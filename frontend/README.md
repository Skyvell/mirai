# Frontend

Vite + React + TypeScript SPA. Architecture lives in `../CLAUDE.md` and `../docs/stack.md`; where a
file goes is decided by `../docs/frontend_filestructure.md`. This file covers only how to run it.

## Toolchain

Package manager is **pnpm**. Do not run `npm install` here — it writes a `package-lock.json` and
desyncs the pnpm store. All commands below run from `frontend/`.

## Commands

```bash
pnpm install     # install deps from pnpm-lock.yaml; after clone and after any package.json change
pnpm dev         # dev server on http://localhost:5173, hot reload
pnpm build       # tsc -b (typecheck) then vite build -> dist/
pnpm lint        # oxlint (--fix to autofix); config in .oxlintrc.json
pnpm preview     # serve the built dist/ locally, to check the production bundle
pnpm generate:api  # regenerate the API client from the backend's OpenAPI schema
```

`pnpm dev` also runs the TanStack Router plugin (`vite.config.ts`), which regenerates
`src/routeTree.gen.ts` whenever a file under `src/routes/` changes.

## Typechecking

**`pnpm dev` does not typecheck.** Vite strips TypeScript types without checking them, so a type
error surfaces only at build time. `pnpm build` is the gate; `pnpm exec tsc -b` typechecks without
producing a bundle. `tsc -b` is incremental — `pnpm exec tsc -b --force` if a result looks stale.

## API client

`pnpm generate:api` runs `api/scripts/export_openapi.py` through uv, writes `openapi.json`, and
regenerates `src/client/` with `@hey-api/openapi-ts` (`openapi-ts.config.ts`). It needs the API's
deps synced (`uv sync` in `../api`). Run it whenever the API contract changes. `src/client/` is
committed; `openapi.json` is not.

## Adding things

```bash
pnpm dlx shadcn@latest add <name>   # component -> src/components/ui/ per components.json
pnpm add <pkg>                      # runtime dependency
pnpm add -D <pkg>                   # dev dependency
pnpm remove <pkg>
```

Check `../docs/stack.md` before adding a dependency — each choice there is tagged `[MVP]` or
`[LATER]`.

## Environment and the backend

`.env` is committed (both values are public) and points `VITE_API_URL` at the deployed dev API.
`.env.local` is gitignored and takes precedence; it currently points at `http://localhost:8000`, so
`pnpm dev` talks to a local backend:

```bash
cd ../api && uv run uvicorn mirai_api.main:app --reload
```

Comment out `VITE_API_URL` in `.env.local` to use the deployed API instead. Only `VITE_`-prefixed
variables reach the browser, and env files are read at startup — restart the dev server after
editing them.

## Notes

- Never hand-edit `src/routeTree.gen.ts`; it is regenerated on dev and build.
- `node_modules/`, `dist/`, `openapi.json`, `.tanstack/` are gitignored artifacts — safe to delete
  and rebuild.
- No test runner is configured yet; `pnpm lint` and `pnpm build` are the whole gate.
