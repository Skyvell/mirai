from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import lru_cache

from anthropic import AsyncAnthropicVertex
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from mirai_api.core.config import get_settings
from mirai_api.models import Biomarker

_SYSTEM_PROMPT = """\
You extract blood biomarker results from a lab report PDF.

You are given a catalogue of known biomarkers, one per line, formatted as
`slug — display name — canonical unit`. For every result in the report:
- Map it to exactly one catalogue slug. Emit that slug verbatim.
- Copy the value, unit, and reference range exactly as printed. Do NOT convert
  units or values.
- If a result cannot be confidently mapped to a catalogue slug, put it in
  `unmatched` instead of guessing.
Extract the sample collection date if present. Only report results actually
present in the document — never invent values.
"""


class ExtractedMeasurement(BaseModel):
    biomarker_slug: str
    value: float
    unit: str
    reference_low: float | None
    reference_high: float | None


class UnmatchedMarker(BaseModel):
    name: str
    value: str
    unit: str | None


class LabExtraction(BaseModel):
    measured_at: date | None
    measurements: list[ExtractedMeasurement]
    unmatched: list[UnmatchedMarker]


@dataclass
class MappedMeasurement:
    """A measurement resolved to a catalogue biomarker, ready to persist."""

    biomarker: Biomarker
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None


@dataclass
class SkippedMarker:
    name: str
    value: str
    unit: str | None
    reason: str


def _decimal(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def map_extraction(
    extraction: LabExtraction, catalogue_by_slug: dict[str, Biomarker]
) -> tuple[list[MappedMeasurement], list[SkippedMarker]]:
    """Resolve extracted measurements against the catalogue.

    Pure and DB-free. A measurement whose slug is not in the catalogue (a model
    hallucination) is demoted to skipped rather than raising; skipped also
    carries the model's own unmatched markers.
    """
    mapped: list[MappedMeasurement] = []
    skipped: list[SkippedMarker] = [
        SkippedMarker(name=u.name, value=u.value, unit=u.unit, reason="unmatched")
        for u in extraction.unmatched
    ]

    for m in extraction.measurements:
        biomarker = catalogue_by_slug.get(m.biomarker_slug)
        if biomarker is None:
            skipped.append(
                SkippedMarker(
                    name=m.biomarker_slug,
                    value=str(m.value),
                    unit=m.unit,
                    reason="unknown_slug",
                )
            )
            continue
        mapped.append(
            MappedMeasurement(
                biomarker=biomarker,
                value=Decimal(str(m.value)),
                unit=m.unit,
                reference_low=_decimal(m.reference_low),
                reference_high=_decimal(m.reference_high),
            )
        )
    return mapped, skipped


@lru_cache
def _agent() -> Agent[None, LabExtraction]:
    """Cached Pydantic AI agent over Claude on Vertex (built lazily so import
    doesn't require ADC). The model id is the bare first-party string; confirm
    it matches the id published in Vertex Model Garden for the region."""
    settings = get_settings()
    model = AnthropicModel(
        "claude-opus-4-8",
        provider=AnthropicProvider(
            anthropic_client=AsyncAnthropicVertex(
                project_id=settings.gcp_project_id, region=settings.vertex_region
            )
        ),
    )
    return Agent(model, output_type=LabExtraction, system_prompt=_SYSTEM_PROMPT)


def _catalogue_prompt(catalogue: list[Biomarker]) -> str:
    lines = "\n".join(
        f"{b.slug} — {b.display_name} — {b.canonical_unit}" for b in catalogue
    )
    return f"Catalogue of known biomarkers:\n{lines}"


async def parse_lab_pdf(pdf_bytes: bytes, catalogue: list[Biomarker]) -> LabExtraction:
    """Run the LLM over a lab PDF and return the structured extraction."""
    result = await _agent().run(
        [
            _catalogue_prompt(catalogue),
            BinaryContent(data=pdf_bytes, media_type="application/pdf"),
        ]
    )
    return result.output
