# Biomarker series

## Purpose

The biomarker details page plots a marker's measurements over time against the platform's canonical reference and optimal bands. The `series` view, proposed in issue #21, delivers both pre-resolved: each point carries its status, and each band arrives as step segments resolved against the user's sex and age at every date. The payload maps directly onto the inputs of the details chart in `frontend/src/features/details/pages/details.tsx`, so the frontend renders it with axis handling as its only logic.

## Endpoint

`GET /biomarkers/series`, operation id `list_biomarker_series`, replaces `GET /biomarker-series`. It accepts one query parameter:

- `slugs`: repeatable; restricts the response to these biomarkers.

Without `slugs` the response holds every biomarker the user has measured. Each series covers the biomarker's full history, from its first measurement to today. A known slug without measurements is absent from the response, and an unknown slug returns 404. `GET /biomarker-series/{slug}` is removed, since `GET /biomarkers/series?slugs={slug}` serves the same purpose.

## Payload

The response maps each biomarker slug to its points and bands, as shown in Figure 1.

```json
{
  "ldl_cholesterol": {
    "unit": "mmol/L",
    "points": [
      { "date": "2025-03-02", "value": 3.1, "status": "normal" },
      { "date": "2025-09-15", "value": 4.9, "status": "high" },
      { "date": "2026-08-04", "value": 5.0, "status": "normal" }
    ],
    "bands": {
      "reference": [
        { "start": "2025-03-02", "end": "2026-01-10", "low": 1.4, "high": 4.7 },
        { "start": "2026-01-10", "end": "2026-11-02", "low": 2.0, "high": 5.3 }
      ],
      "optimal": []
    }
  }
}
```

*Figure 1. Series payload for LDL cholesterol of a man born 1975-01-10, whose reference band steps at age 51.*

Each entry states the `unit` of all its values and bounds, currently the biomarker's canonical unit. Each point holds the draw date, the value and its status, one of `low`, `normal`, `optimal`, `high` or `null`. Each band segment holds a start date, an exclusive end date and inclusive lower and upper bounds; a `null` bound marks a one-sided band, which the client extends to the axis edge. Values and bounds are JSON numbers. The response orders biomarkers by slug, points by date and segments by start, all ascending. Display name comes from `GET /biomarkers/catalogue`, which the details page already holds.
## Chart encoding

The payload describes the data in plot coordinates: points form a time series in date × value space, and each band segment is a rectangle in that same space with corners `(start, low)` and `(end, high)`. Charting libraries consume both directly, points as a keyed data array and segments as reference areas, so the payload stays library-agnostic. Two transforms remain on the client. A `null` bound is replaced by the matching axis limit, since only the chart knows its axis domain. Libraries that draw bands as range series take two step points per segment, `(start, low, high)` and `(end, low, high)`. In the current ECharts implementation, points feed `dataset.source` with `encode: { x: 'date', y: 'value' }`, `status` sets each symbol's size and colour, and each segment becomes one `markArea` rectangle with its dashed bound lines.

## Band resolution

Bands derive from the `biomarker_intervals` rows for the user's sex. A row applies at a date when the user's age in days, `(date - date_of_birth).days`, lies in `[age_min_days, age_max_days)`, with a `null` maximum open-ended. Each row therefore covers the calendar span `[date_of_birth + age_min_days, date_of_birth + age_max_days)`, and its segment is that span clipped to the window `[first measurement, today + 1 day)`, so segments step wherever the user's age crosses a stratum boundary. Spans outside the window are dropped, and ages without a row, such as ferritin before 18 years, leave a gap.

## Status

Status compares a point's value with the bands applying at its date, bounds inclusive, in this order:

1. Without a reference band at that date, the status is `null`.
2. A value below the reference band is `low`.
3. A value above the reference band is `high`.
4. Without an optimal band, a value inside the reference band is `normal`.
5. A value outside the optimal band is `normal`.
6. Otherwise the value is `optimal`.

## Incomplete inputs

A user without `sex` or `date_of_birth` receives empty band lists and `null` status on every point. A measurement stored in a unit other than the biomarker's `canonical_unit` has `null` status until unit conversion lands, after which every value is reported in the canonical unit.

## Deviations from issue #21

The issue lists `from` and `to` window parameters and the band on each point. This design omits both. A single marker's lab history is small enough to load whole, the details chart zooms on the client, and optional window parameters can be added later without breaking existing calls. Points carry status alone, because the plotted band supplies a draw's bounds on hover.
