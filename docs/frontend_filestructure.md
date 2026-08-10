# Frontend Project Structure

```text
src/
├── client/                     # @hey-api output. Never edited, never moved.
├── routes/                     # Route config only, ~6 lines each
│   ├── __root.tsx              # Clerk boundary + <Outlet/>
│   ├── _authenticated.tsx      # profile gate + nav shell
│   └── _authenticated/
│       ├── index.tsx           # /
│       ├── biomarkers/index.tsx
│       ├── sources/
│       │   ├── index.tsx
│       │   └── $uploadId.review.tsx
│       ├── settings.tsx
│       └── {wearables,omics,insights,interventions}.tsx   # placeholders
├── features/
│   ├── biomarkers/
│   │   ├── api.ts              # composed options + invalidation
│   │   ├── pages/
│   │   └── components/         # biomarker-select, manual-entry-form
│   ├── lab-uploads/            # own entity + lifecycle; produces measurements
│   │   ├── api.ts              # invalidation
│   │   ├── status.ts           # IN_PROGRESS, POLL_MS, status label/variant maps
│   │   ├── review-page.tsx
│   │   └── components/         # upload-tab, report-section, draft-items-table
│   ├── profile/
│   │   ├── schema.ts           # zod + parseDateOfBirth (form only)
│   │   ├── completeness.ts     # isProfileComplete — dependency-free on purpose
│   │   ├── settings-page.tsx
│   │   └── components/         # profile-form, onboarding
│   ├── sources/                # fan-in: where your data comes from
│   │   ├── sources-page.tsx
│   │   └── add-data-dialog.tsx # tab registry; each feature owns its tab
│   └── overview/
│       └── overview-page.tsx
├── components/                 # ui/ (shadcn) + domain-agnostic app components
├── lib/                        # api, utils (cn), text — dates use date-fns directly
├── main.tsx
└── routeTree.gen.ts
```

## Rules

1. **Layer direction is one way:** `lib/`, `components/` → `features/` → `routes/`. `src/client/` is a leaf importable by anything and edited by nothing.
2. **A feature is a coherent slice** — usually a nav destination, sometimes an entity with its own lifecycle (`lab-uploads`), sometimes a fan-in page (`overview`, `sources`). No directory without code: `wearables`, `omics`, `insights` and `interventions` keep placeholder JSX in the route file until built.
3. **Features may depend on features, one way.** Current direction — `biomarkers`/`profile` depend on nothing; `lab-uploads` → `biomarkers`; `sources` → `lab-uploads`; `overview` → the domains it summarises. Enforced by `import/no-cycle`; the direction itself is convention.
4. **Ingestion belongs to whatever owns the lifecycle.** `lab-uploads` is a sibling of `biomarkers`, not a child: its own table, status machine and audit rows, and a `failed` upload never becomes biomarker data. Wearables arrive by server-side API integration, so `features/wearables/` will hold only an OAuth connect tab and a connection row. Partner labs POST straight into the API, so the client does nothing.
5. **Fan-in features arrange; contributors self-fetch.** A contributed section owns its query, polling, empty state and rows, so the fan-in page touches no other feature's types or query keys. `lab-uploads/components/report-section.tsx` keeps the `listLabUploadsOptions` query together with the `IN_PROGRESS`-keyed `refetchInterval` — splitting those is the bug. Sources renders sections ("Reports", later "Connected devices"), not one merged list.
6. **Routes are config, not UI.** `createFileRoute` plus the non-splittable critical config (`validateSearch`, `loader`, `beforeLoad`) and a one-line render of a feature page. URL and code layout are decoupled: `/sources/$uploadId/review` renders `features/lab-uploads/review-page.tsx`.

   **A feature page never imports its route file** — that inverts rule 1 and cycles. It takes params and search as props from the thin route, or uses `getRouteApi()`. Reaching for `Route.useParams()` inside the page is the natural move and the wrong one; `import/no-cycle` catches it, because the route already imports the page.
7. **Query keys and API types come from `src/client/`.** Never hand-written. A feature `api.ts` may wrap generated options; it never redefines a key.
8. **Grouping lands as soon as a cohesive group has two members** — `pages/`, `components/` — with no file-count trigger, since a trigger only guarantees a second pass over the same files. A *group* needs cohesion, so `api.ts` and `status.ts` stay at the feature root.
9. **kebab-case files and folders, PascalCase exports.** macOS is case-insensitive and CI is not, so a case-only rename can pass locally and break the build. Number follows the backend convention — plural for a collection surface (`routers/lab_uploads.py`), singular for one entity or a mass noun (`models/lab_upload.py`, `me.py`). Hence `features/lab-uploads/` but `features/profile/` and `features/overview/`.
10. **`components/` is for domain-agnostic UI.** Domain-typed UI stays in its feature even when another feature imports it (`BiomarkerSelect` takes `BiomarkerRead[]`). Promotion requires being useful without knowing any domain type.

## Pinned paths

- `src/lib/api.ts` — `openapi-ts.config.ts` sets `runtimeConfigPath: './src/lib/api'` and generated `client.gen.ts` imports it. Moving it breaks `pnpm generate:api`.
- `src/lib/utils.ts`, `src/components/ui/` — `components.json` aliases drive where `shadcn add` writes and how registry components import each other. `cn` stays in `utils.ts`.
- `src/client/` — `output.clean` empties it on every run.

## Rejected, and why

Kept because these are the decisions most likely to be silently re-introduced.

- **`api/{requests,queries,mutations,query-keys,types}.ts` per feature** — hey-api already generates keys and every type; a hand-written factory is a second source of truth that loses on each spec change. One `api.ts`, for composition only.
- **Pre-created `wearables/providers/*`, `omics/{genomics,…}`** — scaffolding for unbuilt code. Directories follow files.
- **`domains/`** — Overview composes several features and has no model of its own; Sources arranges other features' data. Neither is a domain.
- **Mutual isolation of features** (bulletproof-react's `import/no-restricted-paths` zones) — one hand-written rule per feature, and it breaks on real code: the review page needs `BiomarkerSelect`.
- **An `app/` or `shell/` composition layer** — would make Overview the one nav item without a feature, and become the folder every feature change touches. Cross-feature pages work as features.
- **`sources/` owning ingestion pipelines** — with wearables on server-side API integration and partner labs POSTing, the shared parent had exactly one member.

## Lint

`import/no-cycle` is **partial** enforcement: it catches a feature importing its own route (inherently cyclic, and the likeliest way to break rule 6) but nothing else. A layer inversion that isn't a cycle — `components/` importing a feature, `lib/` importing a feature, a feature importing an unrelated route — passes silently. Rules 1 and 3 are convention, not guardrail; treat the direction table as something a reviewer checks.

A directory-wide ban on `@/routes/*` is **not** expressible in oxlint 1.71: it implements `no-restricted-imports` with `paths` (exact specifiers) but not `patterns` (globs), and has no `import/no-restricted-paths` at all. Verified against the binary — do not re-add a `patterns` rule expecting it to fire, it is silently ignored. If the direction is ever worth real enforcement, `dependency-cruiser` expresses layer rules with globs in ~15 lines.

## Known exemptions

- **The four placeholder routes** (`wearables`, `omics`, `insights`, `interventions`) hold their `<Page/>` inline, so rule 6's "one-line render of a feature page" does not hold for them. Deliberate: they get a feature directory when they get real code (rule 2), and the move is 5 lines either way.
- **Bundle cost of the layout route.** `_authenticated.tsx` is code-split (unlike `__root.tsx`), so anything it imports statically becomes a second network wave in front of the `/me` query that gates every route — and in front of the backend's scale-to-zero cold start. `Onboarding` and the Add-data tabs are therefore `React.lazy`, and `completeness.ts` is kept free of zod/date-fns for the same reason. Before adding a static import here, check what chunk it drags in. Removing the extra wave entirely needs `queryClient` in router context so `/me` can move to a `loader` — not done yet.
