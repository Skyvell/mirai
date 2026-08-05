from dataclasses import dataclass

from mirai_api.integrations.lab_parsing import (
    ExtractedMeasurement,
    LabExtraction,
    UnmatchedMarker,
)
from mirai_api.models import Biomarker


@dataclass
class MappedMeasurement:
    """An extracted measurement resolved to its catalogue biomarker."""

    biomarker: Biomarker
    measurement: ExtractedMeasurement


def map_extraction(
    extraction: LabExtraction,
    catalogue: list[Biomarker],
) -> tuple[list[MappedMeasurement], list[UnmatchedMarker]]:
    """Resolve extracted measurements against the catalogue.

    Pure and DB-free. A measurement whose slug is not in the catalogue (a model
    hallucination) is demoted to unmatched rather than raising; the unmatched
    list also carries the model's own unmatched markers.
    """
    by_slug = {b.slug: b for b in catalogue}
    mapped: list[MappedMeasurement] = []
    unmatched: list[UnmatchedMarker] = list(extraction.unmatched)

    for m in extraction.measurements:
        biomarker = by_slug.get(m.biomarker_slug)
        if biomarker is None:
            unmatched.append(
                UnmatchedMarker(
                    name=m.biomarker_slug,
                    value=str(m.value),
                    unit=m.unit,
                    reference_low=m.reference_low,
                    reference_high=m.reference_high,
                )
            )
            continue
        mapped.append(
            MappedMeasurement(
                biomarker=biomarker,
                measurement=m,
            )
        )
    return mapped, unmatched


def catalogue_prompt(catalogue: list[Biomarker]) -> str:
    """Render the catalogue as the slug vocabulary the extraction prompt needs."""
    lines = "\n".join(f"{b.slug} — {b.display_name} — {b.canonical_unit}" for b in catalogue)
    return f"Catalogue of known biomarkers:\n{lines}"
