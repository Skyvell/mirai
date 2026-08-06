# Recommended Frontend Project Structure

```text
src/
├── api/
│   ├── generated/
│   │   └── schema.ts
│   ├── client.ts
│   └── api-error.ts
│
├── components/
│   ├── ui/                       # shadcn primitives
│   └── shared/                   # cross-domain app components
│
├── domains/
│   ├── biomarkers/
│   │   ├── api/
│   │   │   ├── requests.ts
│   │   │   ├── queries.ts
│   │   │   ├── mutations.ts
│   │   │   ├── query-keys.ts
│   │   │   └── types.ts
│   │   ├── components/
│   │   ├── pages/
│   │   └── schemas.ts
│   │
│   ├── wearables/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── providers/
│   │   │   ├── oura/
│   │   │   └── apple-health/
│   │   └── schemas.ts
│   │
│   ├── omics/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── shared/
│   │   ├── genomics/
│   │   ├── transcriptomics/
│   │   ├── proteomics/
│   │   └── epigenomics/
│   │
│   └── interventions/
│       ├── api/
│       ├── components/
│       ├── pages/
│       └── schemas.ts
│
├── lib/
│   ├── query-client.ts
│   ├── env.ts
│   ├── auth.ts
│   └── utils.ts
│
├── routes/
│   ├── __root.tsx
│   ├── index.tsx
│   ├── login.tsx
│   ├── _authenticated.tsx
│   └── _authenticated/
│       ├── biomarkers/
│       ├── wearables/
│       ├── omics/
│       └── interventions/
│
├── routeTree.gen.ts
├── router.tsx
├── main.tsx
└── vite-env.d.ts
```

## Rules

- `routes/` follows TanStack Router file-based routing and stays thin.
- `domains/` contains business-specific pages, components, API logic, and schemas.
- `api/generated/` is fully generated from FastAPI OpenAPI and never edited manually.
- `components/ui/` contains shadcn primitives only.
- `components/shared/` contains components reused across unrelated domains.
- Keep page-specific components beside the page until reuse is proven.
- Put shared omics concepts in `domains/omics/shared/`; modality-specific logic stays in its subdomain.
- Put Oura and Apple Health integrations under `domains/wearables/providers/`.
- Define TanStack Query options and query keys inside each domain.
- Pass route params and search state into domain pages rather than importing route files from domains.
