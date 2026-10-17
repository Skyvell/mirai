# API design

Implementation spec for the route regroup and the plot-ready biomarker views. Tracks [issue #21](https://github.com/Skyvell/mirai/issues/21); where the two differ, this document is current.

## 1. Routing conventions

- **Shape.** `/{domain}/{resource}[/{id}[/{action}]]`. A domain segment is a namespace and is never addressed alone. Path IDs are typed (UUID); slugs travel as query filters.
- **Domains.** One per product area: `biomarkers` now; `physiology`, `interventions` later. Identity (`/me`) and ops (`/healthz`, `/readyz`) sit at the root.
- **Sources.** A source feeding one domain nests inside it (`/biomarkers/lab-uploads`). A provider feeding several domains lives under `/integrations/{provider}`.
- **Resources and views.** Resources are stored records with reads and writes. Views are read-only, server-computed shapes for the UI, named for their content (`overview`, `series`), never for a page.
- **Filters.** Narrowing is a query parameter: `?slugs=` (repeatable), `?from=` / `?to=` (ISO dates, inclusive).
- **Writes.** Measurement writes stay bulk and all-or-nothing on the collection. State transitions are `POST …/{action}`.
- **Routers.** One `APIRouter(prefix="/biomarkers")` per router file; `biomarkers.py` and `lab_uploads.py` both mount under it. Internal worker routes keep their own `/internal/...` paths outside the prefix.

## 2. Routes

| Method | Path | Kind | `operation_id` | Change |
|---|---|---|---|---|
| GET | `/biomarkers/catalogue` | resource | `list_biomarkers` | path; adds `description` |
| GET | `/biomarkers/overview` (`?slugs=`) | view | `get_biomarker_overview` | new |
| GET | `/biomarkers/series` (`?slugs=`, `?from=`, `?to=`) | view | `list_biomarker_series` | path; new payload |
| GET | `/biomarkers/measurements` (`?slugs=`, `?from=`, `?to=`) | resource | `list_biomarker_measurements` | new |
| POST | `/biomarkers/measurements` | resource | `create_biomarker_measurements` | path |
| PATCH | `/biomarkers/measurements` | resource | `update_biomarker_measurements` | path |
| DELETE | `/biomarkers/measurements` (`?ids=`) | resource | `delete_biomarker_measurements` | path |
| POST | `/biomarkers/lab-uploads` | resource | `create_lab_upload` | path; renamed from `upload_lab` |
| GET | `/biomarkers/lab-uploads` | resource | `list_lab_uploads` | path |
| GET | `/biomarkers/lab-uploads/{upload_id}` | resource | `get_lab_upload` | path; adds band and status per draft row |
| GET | `/biomarkers/lab-uploads/{upload_id}/file` | resource | `get_lab_upload_file` | new |
| DELETE | `/biomarkers/lab-uploads/{upload_id}` | resource | `delete_lab_upload` | path |
| PATCH | `/biomarkers/lab-uploads/{upload_id}/draft` | resource | `update_lab_draft` | path |
| POST | `/biomarkers/lab-uploads/{upload_id}/confirm` | action | `confirm_lab_upload` | path |
| POST | `/internal/biomarkers/lab-uploads/{upload_id}/parse` | internal | hidden | path |

Removed: `GET /biomarker-intervals` (bands resolve inside the views) and `GET /biomarker-series/{slug}` (use `series?slugs=`). Unchanged: `/me`, `/healthz`, `/readyz`.

## 3. Payloads

View endpoints serialize numbers as JSON numbers (floats) and dates as ISO strings. Resource endpoints keep their current Decimal serialization.

### 3.1 Catalogue

`BiomarkerRead` gains `description: str`, one plain sentence on what the marker measures. Requires a `description` column on the catalogue table and seed text per biomarker.

### 3.2 Overview

Keyed by slug; one entry per biomarker with at least one measurement.

```json
{
  "ldl": {
    "display_name": "LDL cholesterol",
    "unit": "mmol/L",
    "latest": { "id": "…", "date": "2026-08-04", "value": 3.4 },
    "previous": { "id": "…", "date": "2026-04-12", "value": 3.1 },
    "status": "critical",
    "bands": {
      "reference": { "low": null, "high": 3.0 },
      "optimal": { "low": null, "high": 2.6 }
    },
    "trend": { "direction": "rising", "since": "2024-08-11" }
  }
}
```

`bands` are the bands applying today. `previous` is null with a single measurement.

### 3.3 Series

Keyed by slug. Without `from`/`to` the window spans the first measurement to today.

```json
{
  "ldl": {
    "display_name": "LDL cholesterol",
    "unit": "mmol/L",
    "points": [
      {
        "id": "…",
        "date": "2026-08-04",
        "value": 3.4,
        "status": "critical",
        "reference": { "low": null, "high": 3.0 },
        "optimal": { "low": null, "high": 2.6 },
        "source": { "lab_upload_id": "…", "filename": "karolinska-aug.pdf" }
      }
    ],
    "bands": {
      "reference": [{ "from": "2024-01-01", "to": "2026-10-17", "low": null, "high": 3.0 }],
      "optimal": [{ "from": "2024-01-01", "to": "2026-10-17", "low": null, "high": 2.6 }]
    }
  }
}
```

`source` is null for manual entries. Points are sorted by date ascending.

### 3.4 Measurements

Flat list for the details-page table and editing, newest first. Extends `BiomarkerMeasurementRead` with `reference_low`, `reference_high` (the lab-printed range, verbatim) and `source` as in 3.3.

### 3.5 Lab upload file

`GET /biomarkers/lab-uploads/{upload_id}/file` returns the PDF (`application/pdf`, `Content-Disposition: inline; filename=…`). Ownership is resolved through `LabUploadService._resolve`, so another user's upload returns 404. The bytes come from `integrations/storage.download`, run via `run_in_threadpool`.

Streaming through the API keeps keyless auth unchanged; a signed GCS URL would require granting the runtime service account `roles/iam.serviceAccountTokenCreator` on itself.

## 4. Band resolution

One pure function in `services/`, shared by overview, series and the lab-upload draft.

1. **Inputs.** The user's `sex` and `date_of_birth`, the biomarker's intervals (`BiomarkerIntervalRepository.list_intervals`), and a date.
2. **Age.** `age_days = (date - date_of_birth).days`.
3. **Stratum.** Per interval type, the interval with matching `sex` and `age_min_days <= age_days < age_max_days` (a null `age_max_days` is open-ended). At most one matches by the stratum unique constraint; none means no band of that type.
4. **Segments.** Over a window, a new segment starts at each date where the age crosses an `age_min_days` boundary: `date_of_birth + age_min_days`. Segments are clipped to the window.
5. **Status**, ported from `frontend/src/features/biomarkers/domain/status.ts`:
   - outside the reference band → `critical`;
   - no optimal band → `normal`;
   - outside the optimal band → `normal`;
   - otherwise → `optimal`.
   Bounds are inclusive; a null bound is open on that side.
6. **Null status.**
   - Missing `sex` or `date_of_birth`: empty `bands`, `status: null` on every point.
   - Measurement unit differing from the biomarker's `canonical_unit`: `status: null` for that point until unit conversion exists.

## 5. Trend

Computed in the overview service over the user's measurements of one biomarker in the canonical unit, ordered by date.

- **Direction.** Compare the latest value to the previous: a relative change under 1% is `flat`, else `rising` or `falling`.
- **Since.** Walk back from the latest point while each step moves in the same direction; `since` is the date of the earliest point in that run.
- One measurement gives `trend: null`.

The details-page takeaway sentence is composed client-side from `status` and `trend`.

## 6. Frontend

- Regenerate the client (`pnpm generate:api`). Call sites change only for `list_biomarker_series` (new payload), `get_biomarker_series` (removed) and `upload_lab` → `create_lab_upload`.
- Status and band selection come from the API; `domain/status.ts` stops deciding status for API data.
- Invalidation:

| Write | Invalidates |
|---|---|
| measurement create, update, delete | `measurements`, `series`, `overview` |
| lab upload confirm or delete | `lab-uploads`, `measurements`, `series`, `overview` |
| `PATCH /me` (sex, date of birth) | `series`, `overview` |

## 7. Implementation order

1. Prefixed routers and moved paths; internal parse path and `integrations/tasks.enqueue_parse` target together.
2. Band resolution and status as a pure service function, with tests in `tests/services/`.
3. `series` on the new payload; `overview` with `trend`.
4. `GET /biomarkers/measurements` with source and lab reference.
5. Catalogue `description` (migration, seed text).
6. Lab upload `file` endpoint; band and status on draft rows.
7. Remove `/biomarker-intervals`; regenerate the frontend client; move status to API data; wire invalidation.

## 8. Deferred

- Pagination; the `from`/`to` window bounds payloads until then.
- Unit conversion to `canonical_unit`.
- `physiology`, `interventions` and `integrations` routes: direction only, specified when built.
