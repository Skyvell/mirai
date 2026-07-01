# Application Stack

Tags: **[MVP]** = needed for first shippable product · **[LATER]** = add only when the trigger is hit.

## Frontend Stack

### Frameworks — [MVP]
Vite + React + TypeScript. TanStack Router for routing, TanStack Query for data fetching, Tailwind CSS v4 with shadcn/ui for styling. API client generated from the FastAPI OpenAPI schema via @hey-api/openapi-ts (TanStack Query plugin) — wired only once the backend exists.

### Added later when needed — [LATER]
React Hook Form when forms become more complex. ECharts when biomarker visualizations become rich. uPlot when wearable time-series become dense. Astro when SEO/content/marketing matters. pnpm workspace when app + marketing + shared packages grow.

## Backend Stack

### User management — [MVP]
Clerk for authentication. Link Clerk user_id to my own user table in Cloud SQL. No health data in Clerk.

### API — [MVP]
FastAPI on Cloud Run.

### Database — [MVP]
Cloud SQL for Postgres. Contains operational data for the app.

### Storage — [MVP]
Cloud Storage (GCS). Holds user-uploaded lab files (blood-test PDFs); the parsed biomarkers land in Cloud SQL.

### Lakehouse — [LATER]
DuckLake. Metadata in Cloud SQL and file storage in GCS. Add when omics or dense wearable data create analytical scale. Will contain all biological data in the future. Even biomarkers. Medallion architecture.

### Transformation — [LATER]
SQLMesh. Add alongside the lakehouse.
