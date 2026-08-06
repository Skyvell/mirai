# Biomarker page design

Status: design spec for `/biomarkers` (grid) and `/biomarkers/$slug` (detail). Supersedes the placeholder table at `frontend/src/routes/biomarkers.tsx`. Written to be built once and kept: it resolves four of the five open questions in `docs/research.md`, closes the four known gaps in `docs/learnings.md`, and establishes three conventions the next domain (wearables) inherits — domain-scoped modules, a real theme system, and a charting integration that stays inside the design tokens.

## Scope

| Route | File | Job |
|---|---|---|
| `/biomarkers` | `src/routes/biomarkers.index.tsx` | Scan every measured marker: where it stands, which way it moved. |
| `/biomarkers/$slug` | `src/routes/biomarkers.$slug.tsx` | Read one marker's history; correct or remove individual measurements. |

`src/routes/biomarkers.tsx` becomes a bare layout (`createFileRoute('/biomarkers')({})`, no component), mirroring the `sources.tsx` precedent. `routeTree.gen.ts` regenerates — never hand-edited.

## Module structure

`docs/chatgpt_generated_unprocessed/recommended-frontend-project-structure.md` proposes domain-scoped modules with thin routes. Adopt it here, shallowly: this page is the first domain large enough to justify it, and a flat `src/components/` that already holds eleven files will not survive wearables, omics, and interventions.

```
src/domains/biomarkers/
├── components/          Cards, sparkline, status, chart, history table
├── model.ts             View model types + selectors (pure)
├── intervals.ts         Band selection + status derivation (pure)
├── format.ts            Value, unit, range, date formatting
└── queries.ts           Thin wrappers over the generated query options
```

Rules: routes stay thin (resolve params, call the domain page component); the generated client in `src/client/` is never wrapped in hand-written fetch code, only in query-option composition; anything reused by an unrelated domain graduates to `src/components/`. Existing `sources`/`lab-upload` components stay where they are until independently touched — no drive-by migration.

## Direction

The subject is laboratory telemetry: an individual reading their own blood chemistry over years. The register is **instrument panel** — dark, measured, numerals foregrounded, colour reserved for meaning. `frontend/design/biomarker_card_chatgpt_{1..4}.png` sets this direction; it becomes the product's identity, not one page's exception.

**Signature: the band.** A shaded reference-range stripe sits behind every value trace at every scale — 100×28 px in a compact card, 140×32 px in a row card, 320 px on the detail page. One graphic answers both questions a user has ("am I inside my range?", "which way am I moving?"), and it is the only element repeating across all three scales.

Boldness is spent in one place: the gradient rim and outer glow on grid and row cards. Per `docs/learnings.md`, a rim marks a floating, clickable surface among many; the detail page *is* the screen, so it carries no rim and no glow — its chart panel gets a flat hairline border. That restraint is deliberate.

## Theme system

The app renders light-only today; `.dark` tokens exist but are dormant, and `ui/sonner.tsx` carries the comment *"The app has no theme switcher; sonner's default light theme matches."* Hardcoding `class="dark"` on `<html>` would ship the dark look and leave that debt in place. Build it properly instead.

`src/components/theme-provider.tsx`:

- Modes `dark | light | system`, default `dark`, persisted under `mirai.theme`.
- Resolves `system` through a `matchMedia('(prefers-color-scheme: dark)')` listener, so an OS change repaints live.
- Writes the class to `document.documentElement` and sets `style.colorScheme` so form controls, scrollbars, and the browser chrome follow.
- Exposes `useTheme()` returning the resolved mode — the chart depends on it (see below).
- A three-line inline script in `frontend/index.html` reads `localStorage` and stamps the class before first paint, preventing a light flash. `<meta name="color-scheme" content="dark light">` alongside it.
- `<Toaster theme={resolvedTheme} />` in `main.tsx`; delete the stale comment in `ui/sonner.tsx`.

No switcher UI is required now — the provider is what makes one a five-line addition later, and it is what keeps the light tokens honest rather than dead.

### Tokens

Values change in `:root`/`.dark` per `CLAUDE.md`. New token *names* additionally need one mapping line each in `@theme inline` to exist as Tailwind utilities; that is the only permitted reason to touch that block.

```css
/* .dark — cool-tinted surfaces matching the mockups. */
--background: oklch(0.13 0.006 250);
--card: oklch(0.18 0.010 250);
--panel: oklch(0.21 0.012 250);        /* Nested surface: chart panel, history table. */
--border: oklch(1 0 0 / 8%);
--muted-foreground: oklch(0.70 0.010 250);
--in-range: oklch(0.78 0.13 195);      /* Cyan. The band, and the in-range trace. */
--in-range-foreground: oklch(0.18 0.010 250);
--rim-from: oklch(0.78 0.13 195 / 28%);
--rim-to: oklch(1 0 0 / 4%);
```

Reused rather than duplicated: `--warning` (amber) is the near-limit state, `--destructive` (rose) the out-of-range state. `--chart-1..5` stay untouched, reserved for future multi-series overlays. Light-mode counterparts of every new token are defined at the same time — a token that exists in one mode only is a latent bug the moment the switcher ships.

Also add `--font-mono: 'Geist Mono Variable', monospace`; `font-mono` currently falls through to Tailwind's default stack.

### Status vocabulary

Four states, derived client-side (the wire carries no status field), expressed as a `cva` variant set in line with `ui/badge.tsx`:

| State | Colour | Condition | Label |
|---|---|---|---|
| In range | `--in-range` | Inside the band, clear of the margin | `In range` |
| Near limit | `--warning` | Inside the band, within 10 % of band width of a bound | `Near limit` |
| Out of range | `--destructive` | Outside the band | `Out of range` |
| No range | `--muted-foreground` | No applicable band for this user | `No range` |

The mockups' `SUBOPTIMAL` and `Optimal range` are **not** adopted: `biomarker_intervals` holds 68 rows, all `type = "reference"`, and zero `optimal` rows. Asserting an optimal target the system does not hold is a false claim in a health product. The band reads `Reference range`. The chart and status derivation are written for **two nested bands from the start** — reference plus optimal — and render only what the API returns, so seeding `optimal` later is data, not a rewrite.

One-sided bands (25 of 68 rows; creatinine has an upper bound only) compute the 10 % margin against the single bound using the plotted domain as width proxy.

## Typography

One family, two roles, one new dependency (`@fontsource-variable/geist-mono`):

| Role | Face | Treatment |
|---|---|---|
| Display value | Geist Variable | 300 weight, `tracking-[-0.02em]`. 1.75 rem in compact cards, 3.5 rem on detail. Unit follows at 0.4× size in `--muted-foreground`. |
| Body / UI | Geist Variable | 400/500, existing scale unchanged. |
| Data | Geist Mono | `tabular-nums`. Every table cell, axis tick, delta, and range bound. |

The personality lives in the numeral treatment, because the numerals are the content: a 3.5 rem hairline value with a small muted unit reads as an instrument readout, not a marketing stat. Category eyebrows are 11 px, `uppercase`, `tracking-[0.14em]`, `--muted-foreground`.

## `/biomarkers` — grid page

```
┌────────────────────────────────────────────────────────────────────┐
│ Biomarkers                                        [ ▦ ] [ ☰ ]      │
│ Ten markers tracked. Values come from your uploaded reports.       │
│                                                                    │
│ LIPIDS ─────────────────────────────────────────────────────── 4   │
│ ┌──────────────┐┌──────────────┐┌──────────────┐                   │
│ │ ● LDL chol.  ││ ● HDL chol.  ││ ● Triglyc.   │                   │
│ │ 3.4 mmol/L   ││ 1.6 mmol/L   ││ 1.1 mmol/L   │                   │
│ │ ▁▂▃▅▆ band   ││ ▅▄▃▃▂ band   ││ ▃▃▄▃▃ band   │                   │
│ │ ↑ 9 %  Jan   ││ ↓ 2 %  Jan   ││ → 0 %  Jan   │                   │
│ └──────────────┘└──────────────┘└──────────────┘                   │
│                                                                    │
│ METABOLIC ──────────────────────────────────────────────────── 2   │
```

- **Container.** `Page` grows `width?: 'default' | 'wide'` (`max-w-2xl` → `max-w-6xl`) and `actions?: ReactNode` for the header-right toggle. Both are generic and reusable; no second page shell.
- **Sections.** One per catalogue `category`, in API order — `list_biomarker_series` already returns `(category, display_name)`, so grouping needs no client sort. Header = eyebrow + hairline `border-t` + count. `content-visibility: auto` with a `contain-intrinsic-size` hint on each section, so off-screen categories cost nothing to lay out.
- **Contents.** Only markers with at least one measurement. Discovering what *can* be measured belongs to the Add-data flow, not to a page whose job is reading your own values.
- **View toggle.** shadcn `toggle-group`, two items with `LayoutGrid` / `Rows3` icons and `aria-label`s. Persisted through a shared `usePersistedState` hook (`src/lib/use-persisted-state.ts`): `useSyncExternalStore` over `localStorage`, a Zod-validated read so a corrupt or stale value falls back to the default instead of throwing, and a `storage` listener so two open tabs agree.
- **Responsive.** Grid 3 columns ≥1024 px, 2 ≥640 px, 1 below. Row cards reflow to two lines below 640 px.

### Compact card — `BiomarkerCardCompact`

168 px min-height, `p-4`, `rounded-[--radius-xl]`, `bg-card`, gradient rim; the whole card is a `<Link to="/biomarkers/$slug">`.

```
┌────────────────────────┐
│ ● LDL Cholesterol      │  8 px status dot + 13 px medium, truncate
│                        │
│ 3.4 mmol/L             │  1.75 rem / 300 value, 0.7 rem muted unit
│                        │
│ ╭──────────────────╮   │  100×28 sparkline over the band stripe
│ │▁▂▃▅▆             │   │
│ ╰──────────────────╯   │
│ ↑ 9 %        Jan 2026  │  mono delta, mono date, both muted
└────────────────────────┘
```

### Row card — `BiomarkerCardRow`

64 px, `grid-cols-[1fr_9rem_9rem_5rem]`, hairline dividers, rim on the group rather than per row.

```
┌──────────────────────────────────────────────────────────────┐
│ ● LDL Cholesterol   3.4 mmol/L   ▁▂▃▅▆ band      ↑ 9 %       │
├──────────────────────────────────────────────────────────────┤
│ ● HDL Cholesterol   1.6 mmol/L   ▅▄▃▃▂ band      ↓ 2 %       │
└──────────────────────────────────────────────────────────────┘
```

Both cards are **pure presentational components** taking a `BiomarkerCardModel` — never raw API types plus intervals. The model is built once per render pass by a memoized selector in `model.ts`, so 60 cards do not each re-derive their band and status. Point types are imported from `@/client` (never hand-mirrored, per `docs/learnings.md`); derived fields are the selector's own.

### Sparkline — `Sparkline` (hand-rolled SVG)

ECharts stays off the grid route: 30–60 chart instances for a non-interactive graphic is indefensible, and SVG keeps the grid chunk at its current size.

- `viewBox="0 0 100 28"`, `preserveAspectRatio="none"`, `vector-effect="non-scaling-stroke"` on the trace so the stroke stays 1.5 px at any width.
- Band stripe: `<rect>` y-mapped from the band bounds, fill `--in-range` at 8 %, 1 px dashed edges at 30 %. One-sided → the rect runs from the bound to the domain edge. No band → no stripe.
- Trace in the status colour; terminal point a 2.5 px filled dot.
- y-domain `[min(dataMin, bandLow), max(dataMax, bandHigh)]` padded 8 %, null bounds dropped.
- **Single measurement:** no polyline — a one-point x-scale divides by zero, the gap logged in `docs/learnings.md`. Render the stripe plus one centred dot.
- `aria-hidden`; value and status are already text.

### Delta

`↑ 9 %`, `↓ 2 %`, `→ 0 %` from the latest two points: mono, `--muted-foreground`, and **not** coloured — see the prerequisite below. Valence lives in the status dot alone. Single measurement → date only, no delta.

## `/biomarkers/$slug` — detail page

No outer card. `max-w-4xl`. Two nested `--panel` surfaces: chart and history.

```
← Back to biomarkers

LDL Cholesterol                                    ┌─────────────┐
lipids · LOINC 22748-8                             │ ● In range  │
                                                   └─────────────┘
3.4 mmol/L      ↑ 9 % since Oct 2025 · 4 measurements

┌──────────────────────────────────────────────────────────────────┐
│ 4.5 ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │
│     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░○░░░░  │
│ 4.3 ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄○─────────  │
│     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░○──────────────░░░░░░░░░░  │
│     ░░░░░░░○──────────────○░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│ 1.2 ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │
│      Feb 25      May 25       Oct 25        Jan 26               │
│                                          Reference range 1.2–4.3 │
└──────────────────────────────────────────────────────────────────┘

Measurements                                                    4
┌──────────────────────────────────────────────────────────────────┐
│ 12 Jan 2026   3.4 mmol/L   lab 1.2–4.3   Report ↗    ✎    🗑     │
│ 04 Oct 2025   3.1 mmol/L   lab 1.2–4.3   Report ↗    ✎    🗑     │
│ 18 May 2025   2.9 mmol/L   lab 1.0–4.0   Manual      ✎    🗑     │
│ 02 Feb 2025   2.7 mmol/L   lab 1.0–4.0   Report ↗    ✎    🗑     │
└──────────────────────────────────────────────────────────────────┘
```

### Header

Back link uses the established inline-link class. Title 3xl/600. Sub-line: category eyebrow + LOINC code (see prerequisites). Status pill: 11 px uppercase `tracking-[0.1em]`, background at 12 %, border at 30 %, 6 px dot. Value block 3.5 rem/300 with muted unit, then a mono meta line.

### Chart — ECharts, detail route only

Decision: **ECharts**, resolving the verdict deferred in `docs/research.md`. Interactivity pays here — hover readout over a multi-year history, value-coloured trace, band rendering — and nowhere else in the app.

- **No wrapper library.** `echarts-for-react` is a thin, sparsely maintained class component; a local `useEChart` hook (~50 lines) gives correct `dispose()` on unmount, a `ResizeObserver` instead of a window listener, `setOption` with `notMerge: false` on data change, and no third-party React-19 compatibility risk. Wrapper libraries around imperative canvas APIs are exactly where leaks and stale-instance bugs live.
- **Bundle.** Import from `echarts/core` and register only `LineChart`, `GridComponent`, `TooltipComponent`, `MarkAreaComponent`, `MarkLineComponent`, `VisualMapComponent`, `SVGRenderer`. The measured 570 kB came from the barrel import. The component is `React.lazy`-imported so the grid route never pays, and `autoCodeSplitting` already isolates the route chunk.
- **SVG renderer, not canvas.** Series are tens of points, not thousands: SVG stays crisp at any DPI, prints, is inspectable in DevTools, and ships less code than the canvas renderer.
- **Tokens, not hexes.** Colours are read from `getComputedStyle(document.documentElement)` inside an effect keyed on `useTheme()`'s resolved mode, then pushed via `setOption`. The chart therefore recolours on a theme change instead of silently keeping the old palette — the failure mode a one-shot read at mount would ship, and the answer to the "options live outside the design tokens" objection in `docs/research.md`.
- **Axes.** x `type: 'time'`; day-precision dates are parsed with the existing `parseIsoDate` (local midnight — `new Date('2026-01-12')` is UTC and renders a day early in negative offsets). y `[min(dataMin, bandLow), max(dataMax, bandHigh)]` padded 10 %, `splitLine` in `--border`, mono labels in `--muted-foreground`.
- **Bands.** `markArea` per band — reference at 8 % fill, optimal (when present) nested at 14 % — plus dashed `markLine` rules at each bound at 30 % with the bound as end label. One-sided → area runs to the axis extreme, only the present bound gets a rule. `Reference range 1.2–4.3` is a panel caption, not an in-plot label.
- **Trace colour.** Piecewise `visualMap` over the value axis: out-of-band `--destructive`, within-margin `--warning`, else `--in-range`. Pieces are built from **explicit finite bounds** clamped to the padded domain — `visualMap` crashes on infinite bounds (`docs/learnings.md`).
- **Single measurement:** `showSymbol: true`, no line, x padded ±30 days.
- **Tooltip.** Date, value + unit, that measurement's own lab range, source. `axisPointer` cross in `--border`.
- **Accessibility.** `aria: { enabled: true }` plus a visually-hidden `<table>` carrying the same series, captioned — a canvas or SVG plot is opaque to a screen reader and this is health data. `animation: false` under `prefers-reduced-motion`.
- **Fallback.** While the lazy chunk loads, the panel renders `Sparkline` at 320 px, so the layout never collapses and the band is visible immediately.

### Measurements table — `MeasurementHistory`

One measurement per row, newest first (reverse of the API's ascending order). Columns: date (mono, `d MMM yyyy`) · value + unit (mono) · that row's own lab range · source · actions, right-aligned. `<caption class="sr-only">`, `scope="col"` on headers.

- **Source.** `Report ↗` linking to `/sources/$uploadId/review` when `lab_upload_id` is set, else `Manual`. Per-row lab ranges are shown because they legitimately differ between reports: the canonical band drives the chart, the lab range documents what that report claimed.
- **Edit.** Pencil `Button variant="ghost" size="icon"` with `aria-label`. One row at a time becomes editable in place, reusing the ghost-cell idiom proven in `sources.$uploadId.review.tsx` (`CELL_CLASS`, `field-sizing-content`). Editable: value, unit, date. Focus moves to the value input on entry; `Escape` cancels, `Enter` saves. `updateBiomarkerMeasurementsMutation` with a single-element array (the endpoint is bulk).
- **Remove.** Trash icon button, `AlertDialog` confirm with `AlertDialogAction variant="destructive"`, as `reports-list.tsx` does it. Copy: *"Remove this measurement? 3.4 mmol/L from 12 Jan 2026 is deleted from your record. The source report is kept."*
- **Mutation contract.** Both mutations apply an **optimistic update with rollback**: cancel in-flight queries for the affected keys, snapshot, patch the cache, restore the snapshot in `onError`, invalidate in `onSettled`. A measurement edit that visibly lags behind the click reads as a lost edit in a record-keeping UI. Mutations set `retry: false` — the query-level `retry: 6` cold-start policy is wrong for writes.
- **Keys.** `listBiomarkerSeriesQueryKey()` and `getBiomarkerSeriesQueryKey({ path: { slug } })`. Failures surface as `toast.error(apiErrorMessage(error))` — row actions have no inline slot, per the convention documented in `reports-list.tsx`. Success: `toast.success('Measurement updated' | 'Measurement removed')`.

## Data flow

Both routes declare a TanStack Router `loader` calling `queryClient.ensureQueryData(...)` for their queries. With `defaultPreload: 'intent'` already set in `main.tsx`, hovering a card starts its detail fetch; without loaders the detail page pays a full round trip after mount, and against a scale-to-zero backend that is seconds of blank panel. Components still read through `useQuery`, so the cache stays the single source of truth.

| Route | Queries |
|---|---|
| Grid | `listBiomarkerSeriesOptions`, `listBiomarkersOptions`, `listBiomarkerIntervalsOptions({ interval_type: 'reference' })`, `currentUserOptions` |
| Detail | the same, plus `getBiomarkerSeriesOptions({ path: { slug } })` |

The intervals request fetches all slugs in one call (68 rows, cached 5 min) rather than per-slug — the `slugs` query param exists for a future catalogue an order of magnitude larger, and switching to it is a one-line change.

Router-level failure handling replaces ad-hoc alerts: `errorComponent` per route, and the detail route throws `notFound()` on the 404 from `get_biomarker_series` so an unknown slug renders a real not-found page rather than a red alert box.

### Band selection — `intervals.ts`

```ts
selectBands(bands, sex, ageDays)      // → { reference: Band | null, optimal: Band | null }
deriveStatus(value, bands)            // → 'in-range' | 'near-limit' | 'out-of-range' | 'no-range'
```

Precedence, in order:

1. Rows where `sex === user.sex` and `ageDays ∈ [age_min_days ?? -∞, age_max_days ?? +∞)`.
2. Rows where `sex === null`, same age window.
3. The latest measurement's own `reference_low`/`reference_high`.
4. `null` → `No range`, no band drawn.

`users.sex` and `date_of_birth` are both nullable, so steps 1–2 can be unreachable. `RequireProfile` in `__root.tsx` already blocks the app until both are set, making this defensive rather than routine; when a band is skipped for that reason the detail page shows one muted line linking to `/settings`: *"Reference ranges depend on your sex and date of birth. Add them in Settings."* `ageInDays` joins `ageInYears` in `src/lib/utils.ts`.

### Numeric handling — `format.ts`

Every `value`, `reference_low`, `reference_high`, `low`, and `high` arrives as a **string** (serialized `Numeric(12, 4)`).

- `Number(...)` is applied once, at the derivation boundary, for geometry and comparison only.
- Display and **editing** keep the string: round-tripping a user's `3.40` through `Number` and back yields `3.4`, silently rewriting their precision. Input state is the string; the payload carries the string.
- All formatting lives in this one module — `formatValue`, `formatUnit` (`umol/L` → `µmol/L`, `ug/L` → `µg/L`, `m[IU]/L` → `mIU/L`), `formatRange` (moved from `routes/biomarkers.tsx`), `formatMeasuredAt`. Numbers are not locale-formatted yet; centralising them here means a Swedish decimal comma is one module's change, not a codebase sweep.

## Backend prerequisites

Two schema gaps make correct semantics impossible from the frontend. Both are pre-launch, so per project convention they fold into the `0001` baseline rather than becoming incremental migrations.

1. **`desired_direction` on `biomarkers`** — `lower | higher | within_range`, VARCHAR + CHECK per the repo's enum convention. Without it, whether a rise is good is unencodable: LDL down is good, HDL up is good. This spec therefore renders the delta in neutral grey, because colouring it would assert a direction the data does not support. With the column, the delta gains valence and Insights inherits the same semantics. This is the `docs/research.md` "marker direction" question, and it is cheaper to answer now than after users have history.
2. **`loinc_code` in `BiomarkerRead`** — the column exists on `Biomarker` and is reference data; exposing it is one schema line plus `pnpm generate:api`. The detail sub-line uses it.

Recommended alongside, not blocking: seed `type = 'optimal'` intervals for the markers where a defensible target exists. The chart, status derivation, and vocabulary already handle two bands; only the data is missing.

If either prerequisite is deferred, the page degrades cleanly — neutral delta, no LOINC line — and no component signature changes.

## States

| State | Treatment |
|---|---|
| Loading (grid) | `CardGridSkeleton`, six shimmer cards. `QueryPane` grows `fallback?: ReactNode`; its loading branch is hardwired to `TableSkeleton` today. |
| Loading (detail) | Header skeleton + 320 px panel skeleton. |
| No measurements | `EmptyState`, `Activity` icon: *"No biomarkers yet — upload a blood-test report with Add data and your values appear here."* `EmptyState` grows an `action?: ReactNode` slot rendered through the already-exported, unused `EmptyContent`. |
| Known slug, no data | *"No measurements for LDL Cholesterol yet."* + the same action. |
| Unknown slug | `notFound()` → route `notFoundComponent` with a back link. |
| Request error | Route `errorComponent` wrapping `ApiErrorAlert` + a retry button. |

## Interaction, motion, accessibility

- Card hover: rim brightens, `-translate-y-px`, 150 ms. `focus-visible`: 2 px `--in-range` ring. Cards are `<Link>`s, so keyboard traversal and Enter come free.
- Grid load: cards fade and rise 4 px, staggered 40 ms, capped at the first twelve. Nothing else on the page animates.
- `prefers-reduced-motion: reduce` disables the stagger, the hover translate, and ECharts animation.
- Status is never colour-only: pill and every row carry the word. `--in-range`, `--warning`, and `--destructive` on `--card` all clear 4.5:1 for text; the 8 % band fill is decorative and always paired with a label.
- Every icon-only button has an `aria-label`. The chart has a visually-hidden data table.

## Testing

The frontend has no test runner today. The derivation logic here — age-banded interval selection, one-sided bands, margin arithmetic, single-point series — is the highest bug-density code in the app and is pure, so it is also the cheapest to cover. Add **Vitest + React Testing Library** (`vitest`, `@vitest/ui`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`), with `pnpm test` alongside the existing `lint`/`build` scripts and a CI step in `_deploy-frontend.yml`.

| Layer | Covers |
|---|---|
`intervals.test.ts` | Sex-specific row beats unisex; age window boundaries (half-open); one-sided bands; fallback to the lab range; no band → `no-range`; margin arithmetic at both bounds. |
`format.test.ts` | Unit prettifier; range formatter incl. one-sided and absent; precision preserved through an edit round trip. |
`model.test.ts` | View-model selector: delta from two points, absent for one; newest-first ordering. |
`sparkline.test.tsx` | Single-point series renders a dot and no polyline; band absent renders no stripe. |
Playwright | Both routes in grid and row mode; toggle persists across reload; edit and delete round-trip and update chart plus grid. |

## Files

| Path | Change |
|---|---|
`frontend/index.html` | No-FOUC theme script, `color-scheme` meta. |
`frontend/src/index.css` | Revised `.dark` values; new `--panel`, `--in-range`, `--in-range-foreground`, `--rim-*`, `--font-mono`, and light-mode counterparts; matching `@theme inline` lines. |
`frontend/src/main.tsx` | Mount `ThemeProvider`; pass `theme` to `Toaster`. |
`frontend/src/components/theme-provider.tsx` | New. |
`frontend/src/components/ui/sonner.tsx` | Drop the stale no-switcher comment. |
`frontend/src/components/page.tsx` | Add `width`, `actions`. |
`frontend/src/components/query-pane.tsx` | Add `fallback`. |
`frontend/src/components/empty-state.tsx` | Add `action`. |
`frontend/src/components/card-grid-skeleton.tsx` | New. |
`frontend/src/lib/use-persisted-state.ts` | New. |
`frontend/src/lib/use-echart.ts` | New — instance lifecycle, resize, theme-keyed recolour. |
`frontend/src/lib/utils.ts` | Add `ageInDays`. |
`frontend/src/domains/biomarkers/` | New — `components/`, `model.ts`, `intervals.ts`, `format.ts`, `queries.ts` per the structure above. |
`frontend/src/routes/biomarkers.tsx` | Reduce to a bare layout route. |
`frontend/src/routes/biomarkers.index.tsx` | New — loader + grid page. |
`frontend/src/routes/biomarkers.$slug.tsx` | New — loader + detail page. |

Dependencies: `echarts`, `@fontsource-variable/geist-mono`, shadcn `toggle-group`, and the Vitest set. Client regeneration only if the `loinc_code` prerequisite is taken.

## Verification

1. `pnpm lint`, `pnpm build` (typecheck), `pnpm test` clean.
2. Bundle check: `pnpm build` and confirm the `/biomarkers` route chunk is unchanged within noise, and that ECharts lands in a separate lazy chunk loaded only on the detail route.
3. Drive the real app at `localhost:5173` signed in as the test user; screenshot both routes in grid and row mode, light and dark, and scrutinise before calling the work done.
4. Fixtures to exercise deliberately: one measurement (no line, no delta); creatinine (one-sided band); a marker with no canonical band (`No range`); a manual measurement (no report link); a value outside the band (rose segment); a value just inside a bound (`Near limit`).
5. Round-trip an edit and a delete; confirm chart and grid update without a manual refresh, and that a forced API failure rolls the optimistic change back.
6. Keyboard-only pass across the grid into a detail page, through an inline edit and a delete confirm. Toggle the OS to light mode and confirm the chart recolours live.

## Rejected

- **Recharts** — shadcn's default charting primitive, but `docs/stack.md` names ECharts for biomarkers; no reason to contradict a recorded decision.
- **`echarts-for-react`** — a wrapper over an imperative API is where stale-instance and disposal bugs live; a 50-line local hook is less code and fully owned.
- **Canvas renderer** — series are tens of points; SVG is crisper, printable, inspectable, and smaller.
- **ECharts in the grid** — 30–60 instances for a non-interactive graphic.
- **`class="dark"` on `<html>`** — ships the look and leaves the theme debt, including sonner's hardcoded light theme.
- **shadcn `Card`** — a `div` with default classes and zero behaviour; restyling it for a bespoke rim means overriding everything it supplies (`docs/learnings.md`).
- **Unmeasured markers in the grid** — ten placeholders today, thirty to sixty later, diluting a page whose job is reading your own values.
- **URL search param for the view toggle** — shareable, but the mode is a durable personal preference, not a property of the link.
- **Coloured delta before `desired_direction` exists** — asserts a direction the catalogue does not encode.
- **`Optimal range` / `SUBOPTIMAL` from the mockups** — no `optimal` rows exist.
- **A separate range rail beside the sparkline** — the band-backed sparkline already answers both questions in one graphic.
- **List virtualization** — 60 cards do not need it. Trigger: a page exceeding ~200 cards, at which point `@tanstack/react-virtual` is the tool.

## Open decisions

- **Search and filter.** Ten markers today; category sections plus the toggle suffice. Trigger: the catalogue passing ~25 markers, or a user holding measurements for more than 20.
- **Backend-derived status.** `docs/research.md` asks whether status belongs on the server. Derived client-side here because band selection needs the profile the client already holds. Revisit when a second surface (Insights, notifications) needs the same derivation — at that point it moves to the API and both consumers read it.
- **Locale-aware numbers and dates.** Swedish lab values use a decimal comma. Deferred, but all formatting is confined to `format.ts` so adopting `Intl` is one module's change. Trigger: a non-English locale shipping.
- **Marker education content.** `docs/research.md` lists range explanation and marker education as detail-page candidates. Not designed here; the header sub-line and chart caption are the seams they would attach to.

## Doc follow-ups

On merge: mark ECharts `[MVP]` in `docs/stack.md` (its `[MVP]`/`[LATER]` tags are absent entirely, contrary to `CLAUDE.md`); close the chart-verdict, one-sided-range, and detail-page-content sections in `docs/research.md`; move the domain-module structure from `docs/chatgpt_generated_unprocessed/` into a processed decision doc now that it has a first consumer.
