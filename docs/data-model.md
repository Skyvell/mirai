# Data model

Entity–relationship diagram of the MVP backend schema (blood biomarkers only).
Rendered from the SQLAlchemy models (`api/src/mirai_api/models/`) via a
migrated database, so it matches exactly what the migrations produce.

![Mirai data model](data-model.svg)

Regenerate after a schema change (needs the Graphviz `dot` binary):

```bash
cd api
docker run -d --name erd -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=mirai -p 55433:5432 postgres:17
export DATABASE_URL=postgresql+pg8000://postgres:pw@localhost:55433/mirai
uv run alembic upgrade head
uv run --with sqlalchemy_schemadisplay --with pydot python scripts/render_erd.py
docker rm -f erd
```

## Notes

- **`users`** anchors a Clerk identity; JIT-created on first authenticated
  request. Profile/identity stay in Clerk; `sex` and `date_of_birth` (both
  nullable; `sex` is a `VARCHAR` + `CHECK` enum) are held locally to select the
  applicable biomarker interval band.
- **`biomarkers`** is a seeded, read-only reference catalogue. `slug` is the
  stable internal key; `loinc_code` is for future lab/FHIR integration.
- **`biomarker_intervals`** holds the canonical, platform-owned low/high bands
  plotted behind a biomarker — population `reference` ranges now, `optimal`
  targets later (`type` discriminates; a `VARCHAR` + `CHECK` enum, as is `sex`).
  One row per (biomarker, `type`, `sex`, age band); `NULL` on any axis means "no
  constraint" (any sex, unbounded age). Age is half-open
  `[age_min_days, age_max_days)` in canonical days; either `interval_low`/`_high`
  may be null for a one-sided band. `RESTRICT` on `biomarker_id`. Sourced from
  Karolinska (`source`/`source_url`); the read API projects the biomarker's
  `canonical_unit` rather than storing it.
- **`lab_uploads`** tracks one PDF through its parse lifecycle. `status`
  (`VARCHAR(15)`, non-native enum) moves `queued → processing → awaiting_review
  → confirmed`, with `failed` terminal. The stored object path is derived
  (`users/{user_id}/labs/{id}.pdf`), not a column.
- **`lab_results`** is the raw, per-report source layer: verbatim parsed values,
  mapped and unmatched alike, retained even after confirm as an audit record.
  A null `biomarker_id` is an unmatched marker the user maps; `included` tracks
  keep/drop for confirm. On confirm, included+mapped rows are copied into
  `biomarker_measurements`.
- **`biomarker_measurements`** is the curated record the series API reads.
  `lab_upload_id` is null for manual entries and for measurements whose report
  was deleted (`SET NULL`), so history survives report deletion. `user_id` is
  denormalized (also reachable via the upload) for the per-user time-series read
  path — the composite `INDEX (user_id, biomarker_id, measured_at)` serves it.
- **FK delete behavior:** `CASCADE` from `users` and (for `lab_results`)
  `lab_uploads`; `RESTRICT` on `biomarker_id` (catalogue rows can't be deleted
  out from under data); `SET NULL` on a measurement's `lab_upload_id`.
