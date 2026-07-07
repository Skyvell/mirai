from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import lru_cache

from anthropic import AsyncAnthropicVertex
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from sqlalchemy import select
from sqlalchemy.orm import Session

from mirai_api.core.config import get_settings
from mirai_api.core.db import get_engine
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
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None


class UnmatchedMarker(BaseModel):
    name: str
    value: str
    unit: str | None


class SkippedMarker(BaseModel):
    """A marker that did not become a measurement, with why."""

    name: str
    value: str
    unit: str | None
    reason: str


class LabExtraction(BaseModel):
    measured_at: date | None
    measurements: list[ExtractedMeasurement]
    unmatched: list[UnmatchedMarker]


@dataclass
class MappedMeasurement:
    """An extracted measurement resolved to its catalogue biomarker."""

    biomarker: Biomarker
    measurement: ExtractedMeasurement


def map_extraction(
    extraction: LabExtraction, catalogue: list[Biomarker]
) -> tuple[list[MappedMeasurement], list[SkippedMarker]]:
    """Resolve extracted measurements against the catalogue.

    Pure and DB-free. A measurement whose slug is not in the catalogue (a model
    hallucination) is demoted to skipped rather than raising; skipped also
    carries the model's own unmatched markers.
    """
    by_slug = {b.slug: b for b in catalogue}
    mapped: list[MappedMeasurement] = []
    skipped: list[SkippedMarker] = [
        SkippedMarker(name=u.name, value=u.value, unit=u.unit, reason="unmatched")
        for u in extraction.unmatched
    ]

    for m in extraction.measurements:
        biomarker = by_slug.get(m.biomarker_slug)
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
        mapped.append(MappedMeasurement(biomarker=biomarker, measurement=m))
    return mapped, skipped


@lru_cache
def _agent() -> Agent[None, LabExtraction]:
    """Cached Pydantic AI agent over Claude on Vertex (built lazily so import
    doesn't require ADC)."""
    settings = get_settings()
    model = AnthropicModel(
        settings.vertex_model,
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


@lru_cache
def cached_catalogue() -> tuple[list[Biomarker], str]:
    """The seeded, read-only biomarker catalogue and its prompt, loaded once.

    Detached instances are safe to reuse across requests: only column values are
    read, never relationships. Catalogue changes ship as migrations, which
    redeploy the process and reset this cache.
    """
    with Session(get_engine()) as session:
        catalogue = list(session.scalars(select(Biomarker)))
        session.expunge_all()
    return catalogue, _catalogue_prompt(catalogue)


async def parse_lab_pdf(
    pdf_bytes: bytes, catalogue_prompt_text: str
) -> LabExtraction:
    """Run the LLM over a lab PDF and return the structured extraction."""
    result = await _agent().run(
        [
            catalogue_prompt_text,
            BinaryContent(data=pdf_bytes, media_type="application/pdf"),
        ]
    )
    return result.output
