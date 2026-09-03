# Design for biomarker page

## Description
The biomarker page should display cards in two different ways. Either as rectangular cards in a grid pattern or as horizontal cards stacked as a column. This should be toggleable. When a card is clicked, the user should be sent to the "details page" for that particular biomarker.

## Biomarkers page

### Overview

#### Content
- Number of biomarkers the user has tested for.
- Number currently Optimal.
- Number currently Normal.
- Number currently Critical.
- Date of the most recent measurement.
- An invitation to add data, when the user has no measurements at all.

#### Design

```
8 biomarkers tested            Latest measurement 4 Aug 2026

████████████  ████████████████████████  ████████████
2 Optimal     4 Normal                  2 Critical
```

- One track, three segments, sized by how many markers sit in each. Same bullet-graph grammar as the cards.
- Selecting a segment filters the list below, setting the same state as the status filter in the controls.
- Same status words, same colours, same Optimal → Normal → Critical order as the rest of the page.

With no measurements at all:

```
No biomarkers yet

Upload a lab report and Mirai reads the values into your timeline.
You can also enter a measurement by hand.

[ Upload a report ]   [ Enter manually ]
```

- The overview, the controls and the cards are all replaced by this invitation, which names both routes in.

### Page controls

#### Content
- Search by marker name.
- Filter by status.
- Toggle between the grid of rectangular cards and the stacked row cards, showing which of the two is active.

#### Design

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Search markers       [ All statuses ▾ ]           [ ▦ | ▤ ]  │
└─────────────────────────────────────────────────────────────────┘
```

- One toolbar between the overview and the cards, holding everything that acts on the list rather than on a single marker. The list holds only markers with at least one measurement; untested ones are never rendered as empty cards.
- Always alphabetical, no sort control: alphabetical is stable where status order reshuffles with every new measurement.
- Status has an explicit filter control; selecting a segment in the overview sets the same state. Search filters, never reorders.
- Search and status sit left, the view toggle right. The toggle is one segmented control of two parts with the active part held down, not a single icon that swaps, and it persists between visits.
- Visible keyboard focus on every interactive element; transitions respect reduced motion.
- A category filter is `[LATER]` — trigger: the catalogue exceeds roughly 25 markers.

### Rectangular card

#### Content
- Name of the biomarker.
- Value of the biomarker, with its unit.
- Current status of the biomarker.
- Position of the value within the reference and optimal ranges.
- Change since the previous measurement.
- How long ago it was measured.

#### Design

```
┌────────────────────────────────┐
│ LDL Cholesterol       Critical │
│                                │
│ 3.4 mmol/L                     │
│                                │
│ ───▓▓▓▓████████▓▓▓▓──●──────── │
│    1.8            3.0          │
│                                │
│ ↑ 9 %              3 weeks ago │
└────────────────────────────────┘
```

- Four bands: name and status, value, bullet graph, then trend and recency. Status takes the top-right corner; the value stands alone below it.
- The bullet graph is the card's only chart and the page's signature device: light segment the reference range, the darker segment inside it the optimal range, the dot the latest value. The same grammar recurs in the overview and on the detail chart.
- Bounds printed under the track, small and muted, never behind hover — each bar is normalised to its own range. The row card omits them for lack of a second line.
- Status reads Optimal, Normal, or Critical. Until optimal ranges exist the inner segment is absent and in-range values read Normal.
- Recency is relative, not a date. Grid reflows 1/2/3/4 columns as one flat set, with no category headings and no category label.

### Row card

#### Content
- Name of the biomarker.
- Value of the biomarker, with its unit.
- Current status of the biomarker.
- Position of the value within the reference and optimal ranges.
- Change since the previous measurement.
- How long ago it was measured.

#### Design

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ LDL Cholesterol    3.4 mmol/L  Critical   ──▓▓████▓▓──●───  ↑ 9 %  3 weeks ago│
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ HDL Cholesterol    1.6 mmol/L  Normal     ──▓▓●███▓▓▓─────  ↓ 2 %  3 weeks ago│
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ Triglycerides      1.2 mmol/L  Optimal    ───▓▓██●█▓▓▓────  → 0 %  3 weeks ago│
└───────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│ Glucose (Fasting)  5.4 mmol/L  Normal     ───▓▓███●▓▓▓────  ↑ 4 %  3 weeks ago│
└───────────────────────────────────────────────────────────────────────────────┘
```

- Each marker is its own card — a full-width surface with a gap between it and the next, not a table row. Same fields as the tile on one line: name, then value and status together, then position, then trend and recency.
- Columns align from card to card. Both layouts carry the same fields; the toggle is a density preference. Below the narrow breakpoint the rows collapse to the grid tile and the toggle hides.
- The status word carries the colour; the dot's position relative to the two nested bands is the non-colour cue.
- One flat stack, no category headings or labels. The whole card is the click target, and both views list the same set of markers.

## Details Page

### Summary

#### Content
- Link back to the biomarkers list.
- Marker name, and one plain sentence on what it measures.
- Current value with unit, and its status.
- A plain-language takeaway combining status and direction.
- When it was last tested, both relative and as a date.

#### Design

```
← Biomarkers

LDL Cholesterol
Carries cholesterol into artery walls, where excess builds up as plaque.

3.4 mmol/L   Critical

Above your reference range, and rising for two years.

Last tested 3 weeks ago  ·  4 Aug 2026
```

- Deliberately spare: how far off, how long, and which way are left to the graph below.
- Four things text carries that the chart cannot: the marker named in plain words, the exact number, a verdict, and how fresh the reading is.
- The takeaway sentence is composed from status and direction; it introduces no new data.
- No bullet graph here — the chart directly below is the same encoding plus a time axis.

### Graph

#### Content
- Every measurement of this marker plotted with date on the X axis and value on the Y axis.
- Lower and upper bounds of the platform's canonical reference range.
- Lower and upper bounds of the platform's canonical optimal range, drawn inside the reference range.
- Legend naming the two ranges.
- Time range selector, offering only the spans the history covers.
- Per-point detail on hover, focus or tap: date, value, the canonical ranges applying at that draw, and the report it came from.

#### Design

```
                                                    [ 1Y ] [ 5Y ] [ All ]
mmol/L
 4.0 ┤
     │                                                      ●
 3.5 ┤                                           ●        ╱
     │                                                  ╱
 3.0 ┤     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
     │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 2.5 ┤█████████████████●█████████████████████████████████████
     │█████●█████████████████████████████████████████████████
 2.0 ┤███████████████████████████████████████████████████████
     │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
     └────────┬─────────┬─────────┬─────────┬─────────┬──────
            2022      2023      2024      2025      2026

        ▓ Reference range          █ Optimal range
```

- No summary text on the chart. Only the range selector, top right, offering just the spans the history covers.
- X axis is true calendar time, never one slot per draw, so gaps read as gaps. Tick labels follow the selected range — months at a year, years beyond it. Y axis is the value in the marker's unit on evenly spaced ticks. Both ranges are shaded areas, optimal nested inside reference.
- The bands are the platform's canonical ranges, not any lab's, resolved against the user's sex and age at each draw's date, so they step. No fixed pair of numbers appears on the chart; a draw's bounds appear in its tooltip. The legend below names the two bands, and the same encoding is used on every marker's chart.
- Critical points are filled and larger, in-range points small and quiet, the latest always emphasised. The Y axis covers both bands plus every value in view. Points are focusable and tappable, not hover-only.

### Measurements

#### Content
- Every measurement of this marker, newest first.
- Total number of measurements.
- Date of the draw.
- Value with the unit exactly as reported.
- Reference range printed on the lab report, where the report gave one.
- Change from the previous measurement.
- Where the value came from: the uploaded report, named and linked, or manual entry.
- Edit a measurement's value or date.
- Delete a measurement.

#### Design

```
Measurements                                                        12 measurements

┌─────────────┬─────────────┬────────┬───────────────┬────────────────────┬───────┐
│ Date        │       Value │ Change │ Lab reference │ Source             │       │
├─────────────┼─────────────┼────────┼───────────────┼────────────────────┼───────┤
│ 4 Aug 2026  │  3.4 mmol/L │  ↑ 9 % │     1.8 – 3.0 │ karolinska-aug.pdf↗│ ✎  ✕  │
│ 12 Apr 2026 │  3.1 mmol/L │  ↑ 3 % │     1.8 – 3.0 │ blodprov-apr.pdf  ↗│ ✎  ✕  │
│ 18 Dec 2025 │  3.0 mmol/L │  ↓ 5 % │             — │ Manual entry       │ ✎  ✕  │
└─────────────┴─────────────┴────────┴───────────────┴────────────────────┴───────┘
```

- The record, not the interpretation: what the source said, checkable against its PDF. Source names the uploaded report and links to it, truncating long names from the middle to keep the extension visible, and reads "Manual entry" where there is no report.
- Columns: when, what, how much it moved, then context and provenance. Change is arithmetic between consecutive draws, shown only when they share a unit. Numeric columns right-aligned on the decimal, dates and text left-aligned, actions rightmost.
- Reference is the range the lab printed, verbatim per draw; it can differ between reports and is empty for manual entries. The platform's canonical and optimal ranges stay on the graph. No status colour here — a value can sit inside the lab's range and outside the platform's.
- Two small icon buttons in the rightmost column of every row: edit, then delete. Editing turns the value and date cells into inputs in place; deleting asks for confirmation and names the measurement being removed.
- Below the narrow breakpoint each measurement becomes a block: date, value and change on the first line, lab reference and source beneath, actions at the foot.

### Why it matters `[LATER]`

Trigger: reviewed explanatory copy exists for every marker in the catalogue. Nothing is built until then, and no placeholder medical text enters the codebase.

#### Content
- What the marker does in the body.
- What raises or lowers it.
- What an out-of-range result implies, and when it is worth raising with a doctor.
- Where the explanation comes from.
- A note that this describes the marker in general, not the reader's own result.

#### Design

```
Why it matters

What LDL cholesterol does
Two or three plain sentences, no clinical vocabulary.

What raises or lowers it
Two or three plain sentences.

What a result outside the range means
Two or three plain sentences, including when it is worth
raising with a doctor.

Source: Karolinska Universitetslaboratoriet
General information about the marker, not advice about your result.
```

- Prose, not tiles, and it reads last.
- Three fixed subheadings in the same order for every marker.
- Every block carries its source and states that it describes the marker in general, not the reader's own result.
- Distinct from Summary's one-line description, which stays in MVP.
