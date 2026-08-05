# Preliminary test design

Status: preliminary — open decisions listed at the end.

## Shape

A three-layer pyramid. Each layer covers what the layer below cannot, at the
lowest cost that still exercises the real behavior.

| Layer | Runs | Covers | Cost |
|---|---|---|---|
| Unit | `pytest` + fakes (exists) | Pure logic, routers, service branches | ms, no I/O |
| Integration | `pytest` + Postgres container | Real SQL: FK `CASCADE`/`SET NULL`, the `queued→processing` CAS, `confirm→measurements` copy, `updated_at` `onupdate` | seconds |
| E2e | Playwright, full stack local | Core user journeys through UI→API→DB | tens of seconds |

Unit stays the fast base; integration is where DB logic is verified precisely;
e2e is a thin smoke of top journeys, not where DB semantics are covered.

## Prerequisite: `DATABASE_URL` seam

`core/db.py::get_engine` is Cloud SQL-only today. Add a `DATABASE_URL` override
(mirroring `alembic/env.py`): set → `create_engine(url)`, unset → Cloud SQL. This
single seam lets the app and tests target a local/container Postgres. Nothing
DB-backed runs locally without it.

## Local runnability without GCP

The app already degrades to a local-friendly path; only two externals need fakes.

| Dependency | Local handling |
|---|---|
| Cloud SQL | Local Postgres (Docker Compose) via the `DATABASE_URL` seam |
| Cloud Tasks | Already synchronous when `WORKER_BASE_URL` is empty (`submit` runs `process` in-request) |
| GCS | Fake behind `integrations/storage.py` — emulator (`fake-gcs-server`) or a filesystem backend |
| Anthropic | Stubbed in tests (`parse_lab_pdf` seam); capped dev key for manual runs |

Result: the full upload→review→confirm flow runs locally with no GCP — local
Postgres + fake GCS + synchronous, stubbed parse.

## Tooling

- Integration: `testcontainers[postgres]`; session fixture runs
  `alembic upgrade head`, per-test transaction rollback for isolation. Same
  mechanism locally and in CI (runners have Docker).
- E2e: `@playwright/test` + `@clerk/testing` (programmatic sign-in, bypasses
  Turnstile) against a local full stack, `E2E_BASE_URL`-parameterized. LLM upload
  path asserted tolerantly (reaches `awaiting_review`, draft present, confirm
  succeeds) or run with a stubbed parser.
- Orchestration: `compose.yaml` (Postgres, optional fake-gcs) + `just` targets
  (`db-up`, `migrate`, `test`, `e2e`).

## CI

CI is deploy-only today. Add a test gate before deploy: `pytest` (unit +
integration) + `ruff`, and frontend `tsc` + `oxlint`; deploy jobs `needs: test`.
Optional post-deploy smoke against dev (`/readyz` + one authed call) validates the
real Cloud SQL/IAM/CORS path that local fakes cannot.

## Rejected

Ephemeral Cloud SQL per CI run: ~5–15 min provisioning each way, flaky, costs
money, and adds nothing over a container (same Postgres engine). The real
connector/IAM path is already exercised by the `mirai-migrate` deploy job and
`/readyz`.

## Open decisions

- Keep integration, or run only unit + local e2e (thinner, but DB bugs surface
  slower and less precisely).
- GCS fake: `fake-gcs-server` emulator vs. a filesystem storage backend.
- E2e primary target: local full stack (deterministic, free) vs. post-deploy
  against dev (real infra, nondeterministic) — or both.
