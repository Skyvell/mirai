# Frontend

## Toolchain

Package manager is **pnpm**. Do not run `npm install` here — it writes a `package-lock.json` and
desyncs the pnpm store. All commands below run from `frontend/`.

## Commands

```bash
pnpm install     # install deps from pnpm-lock.yaml; after clone and after any package.json change
pnpm dev         # dev server on http://localhost:5173, hot reload; talks to the deployed API
pnpm dev:localapi  # same, against a local backend on :8000
pnpm build       # tsc -b (typecheck) then vite build -> dist/
pnpm lint        # oxlint (--fix to autofix); config in .oxlintrc.json
pnpm preview     # serve the built dist/ locally, to check the production bundle
pnpm generate:api  # regenerate the API client from the backend's OpenAPI schema
```

`pnpm dev` also runs the TanStack Router plugin (`vite.config.ts`), which regenerates
`src/routeTree.gen.ts` whenever a file under `src/routes/` changes.

## Adding dependencies and components

```bash
pnpm dlx shadcn@latest add <name>   # component -> src/components/ui/ per components.json
pnpm add <pkg>                      # runtime dependency
pnpm add -D <pkg>                   # dev dependency
pnpm remove <pkg>
```
