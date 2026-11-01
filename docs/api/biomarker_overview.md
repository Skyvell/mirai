# Biomarker overview

## Purpose

The biomarkers page shows a header summarising the user's markers and one card per measured marker. The `overview` view, proposed in issue #21, serves both with every value pre-resolved, so the frontend renders the response exactly as received. Band resolution and status follow `docs/api/biomarker_series.md`, so a card and the latest point on the marker's chart always agree.

## Endpoint

`GET /biomarkers/overview`, operation id `get_biomarker_overview`, returns every biomarker the user has measured.

## Payload

The response holds a `summary` for the page header and a `biomarkers` array with one item per measured marker, as shown in Figure 1.

```json
{
  "summary": {
    "latest_date": "2026-08-04",
    "counts": { "optimal": 0, "normal": 1, "low": 0, "high": 1 }
  },
  "biomarkers": [
    {
      "slug": "hdl_cholesterol",
      "display_name": "HDL cholesterol",
      "unit": "mmol/L",
      "latest": { "date": "2026-08-04", "value": 1.6, "status": "normal" },
      "change": -0.02,
      "bands": {
        "reference": { "low": 0.8, "high": 2.1 },
        "optimal": null
      }
    },
    {
      "slug": "ldl_cholesterol",
      "display_name": "LDL cholesterol",
      "unit": "mmol/L",
      "latest": { "date": "2026-08-04", "value": 5.4, "status": "high" },
      "change": 0.08,
      "bands": {
        "reference": { "low": 2.0, "high": 5.3 },
        "optimal": null
      }
    }
  ]
}
```

*Figure 1. Overview payload for a man aged 51 with two measured markers.*

### Summary

`latest_date` is the most recent draw date across all measured markers. `counts` holds the number of markers per latest status, always listing all four statuses in the order the header draws them: `optimal`, `normal`, `low`, `high`. A marker with `null` status is listed in `biomarkers` only. The number of markers tested is the length of `biomarkers`. An account without measurements receives `latest_date: null`, zero counts and an empty `biomarkers` array, which the page renders as its empty-state invitation.

### Items

Items are ordered by `display_name`, the order the cards render. Each item holds the marker's `slug` for linking, its `display_name`, the `unit` of all its values and bounds, its `latest` measurement, the relative `change` from the previous measurement and the `bands` applying to the latest measurement. Display name is a projection of the catalogue, carried here because a view serves its consumer whole.

`latest` uses the series point shape: draw date, value and status, one of `low`, `normal`, `optimal`, `high` or `null`. Measurements sharing a draw date are ordered by entry time, so the later entry counts as more recent. `change` is the unrounded relative change between the two most recent measurements as a fraction, `0.08` meaning a rise of 8 %. It is `null` with a single measurement, with a previous value of zero, or when either value is in a unit other than the biomarker's `canonical_unit`. Each band is `{ low, high }` with inclusive bounds, a `null` bound marking a one-sided band; a band absent at that age is `null`. Values and bounds are JSON numbers.

## Band resolution

Bands resolve by the series rule at the date of the latest measurement: the user's age in days at that date selects the `biomarker_intervals` row for the user's sex, per band type. `latest.status` derives from the same bands by the status rules of `docs/api/biomarker_series.md`. A card therefore shows the reading as interpreted for the user's age when it was drawn.

## Incomplete inputs

A user without `sex` or `date_of_birth` receives `null` for both bands and for the status of every item. A latest measurement in a unit other than the biomarker's `canonical_unit` has `null` status until unit conversion lands.

## Deviations from issue #21

The issue lists a `slugs` filter, and per marker the previous value, the bands applying today and a `trend`. This design drops `slugs`, since the page always loads every marker, replaces the previous value with the precomputed `change`, resolves bands at the latest measurement's date so they agree with its status, and omits `trend`, since the page shows movement only as the change between the last two measurements. The `summary` block is an addition that moves the page header's aggregation to the server.
