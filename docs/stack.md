# Application Stack

## Frontend Stack

### Frameworks
- Vite + React + TypeScript.
- TanStack Router.
- TanStack Query.
- Tailwind CSS v4.
- shadcn/ui for styling.
- React Hook Form (when forms become more complex).
- ECharts (biomarkers).
- uPlot (wearables).
- Astro (SEO/content/marketing) matters.

## Backend Stack

### User management
Clerk for authentication. Link Clerk user_id to my own user table in Cloud SQL. No health data in Clerk.

### Migrations
- Alembic.

### API
FastAPI on Cloud Run.

### Database
- Cloud SQL for Postgres. Contains operational data for the app.

### Storage
- Cloud Storage (GCS).

### Parsing
- Claude, Anthropic API.

### Lakehouse
DuckLake. Metadata in Cloud SQL and file storage in GCS. Add when omics or dense wearable data create analytical scale. Will contain all biological data in the future. Even biomarkers. Medallion architecture.

### Transformation
SQLMesh. Add alongside the lakehouse.
