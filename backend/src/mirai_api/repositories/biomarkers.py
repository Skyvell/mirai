import uuid
from collections.abc import Iterable

from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session, contains_eager

from mirai_api.models import Biomarker, BiomarkerMeasurement


class BiomarkerRepository:
    """Database access for biomarkers and their measurements.

    Write methods flush but never commit; the owning service calls commit()
    as the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_biomarkers(self) -> list[Biomarker]:
        """Return the full catalogue, ordered for display."""
        return list(
            self._session.scalars(
                select(Biomarker).order_by(
                    Biomarker.category,
                    Biomarker.display_name,
                )
            )
        )

    def get_biomarkers(self, slugs: Iterable[str]) -> list[Biomarker]:
        """Return the biomarkers matching the given slugs; missing slugs are absent."""
        return list(self._session.scalars(select(Biomarker).where(Biomarker.slug.in_(slugs))))

    @staticmethod
    def _user_measurements(user_id: uuid.UUID) -> Select[tuple[BiomarkerMeasurement]]:
        """Base select: user-scoped, with the biomarker join eager-loaded."""
        return (
            select(BiomarkerMeasurement)
            .join(Biomarker, BiomarkerMeasurement.biomarker_id == Biomarker.id)
            .options(contains_eager(BiomarkerMeasurement.biomarker))
            .where(BiomarkerMeasurement.user_id == user_id)
        )

    def list_measurements(
        self,
        user_id: uuid.UUID,
        slug: str | None = None,
    ) -> list[BiomarkerMeasurement]:
        """Return the user's measurements, ordered for series grouping.

        The ORDER BY is the series contract: the first three keys set the
        series order and make each biomarker's rows contiguous for grouping;
        the last two set the within-series order.
        """
        stmt = self._user_measurements(user_id).order_by(
            Biomarker.category,
            Biomarker.display_name,
            Biomarker.slug,
            BiomarkerMeasurement.measured_at.nulls_last(),
            BiomarkerMeasurement.created_at,
        )
        if slug is not None:
            stmt = stmt.where(Biomarker.slug == slug)
        return list(self._session.scalars(stmt))

    def get_measurements(
        self,
        user_id: uuid.UUID,
        ids: Iterable[uuid.UUID],
    ) -> list[BiomarkerMeasurement]:
        """Return the user's measurements matching the given ids."""
        return list(
            self._session.scalars(
                self._user_measurements(user_id).where(BiomarkerMeasurement.id.in_(ids))
            )
        )

    def add_measurements(self, measurements: list[BiomarkerMeasurement]) -> None:
        """Stage new measurements; the flush materializes their ids."""
        self._session.add_all(measurements)
        self._session.flush()

    def delete_measurements(
        self,
        user_id: uuid.UUID,
        ids: Iterable[uuid.UUID],
    ) -> set[uuid.UUID]:
        """Delete the user's measurements matching ids; return the deleted ids."""
        deleted = self._session.execute(
            delete(BiomarkerMeasurement)
            .where(
                BiomarkerMeasurement.id.in_(ids),
                BiomarkerMeasurement.user_id == user_id,
            )
            .returning(BiomarkerMeasurement.id)
        )
        return set(deleted.scalars())

    def commit(self) -> None:
        """Transaction boundary; called only by the owning service."""
        self._session.commit()
