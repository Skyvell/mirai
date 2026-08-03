from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager

from mirai_api.core.enums import IntervalType
from mirai_api.models import Biomarker, BiomarkerInterval


class BiomarkerIntervalRepository:
    """Read access for canonical biomarker intervals; read-only, never commits."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_intervals(
        self,
        slugs: list[str] | None = None,
        interval_type: IntervalType | None = None,
    ) -> list[BiomarkerInterval]:
        """Return intervals with their biomarker eager-loaded, in output order.

        The ORDER BY gives a deterministic biomarker order (slug) and, within each
        biomarker, orders the bands by age into step segments.
        """
        stmt = (
            select(BiomarkerInterval)
            .join(Biomarker, BiomarkerInterval.biomarker_id == Biomarker.id)
            .options(contains_eager(BiomarkerInterval.biomarker))
            .order_by(
                Biomarker.slug,
                BiomarkerInterval.type,
                BiomarkerInterval.sex,
                BiomarkerInterval.age_min_days.asc().nulls_first(),
            )
        )

        # Optional slug filter; absent means the whole table.
        if slugs is not None:
            stmt = stmt.where(Biomarker.slug.in_(slugs))

        # Optional type filter; absent means every interval type.
        if interval_type is not None:
            stmt = stmt.where(BiomarkerInterval.type == interval_type)

        return list(self._session.scalars(stmt))
