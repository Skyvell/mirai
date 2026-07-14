import uuid
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from mirai_api.models import DraftBiomarkerMeasurement


class DraftBiomarkerMeasurementRepository:
    """Database access for draft measurements awaiting review.

    Write methods flush but never commit; the owning service commits the
    session as the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_all(self, drafts: list[DraftBiomarkerMeasurement]) -> None:
        """Stage new draft rows; the flush materializes their ids."""
        self._session.add_all(drafts)
        self._session.flush()

    def list_for_upload(self, upload_id: uuid.UUID) -> list[DraftBiomarkerMeasurement]:
        """Return an upload's draft rows, biomarker eager-loaded, in insertion order."""
        return list(
            self._session.scalars(
                select(DraftBiomarkerMeasurement)
                .options(joinedload(DraftBiomarkerMeasurement.biomarker))
                .where(DraftBiomarkerMeasurement.lab_upload_id == upload_id)
                .order_by(DraftBiomarkerMeasurement.id)
            )
        )

    def get_for_upload(
        self,
        upload_id: uuid.UUID,
        ids: Iterable[uuid.UUID],
    ) -> list[DraftBiomarkerMeasurement]:
        """Return an upload's draft rows matching the given ids, biomarker eager-loaded."""
        return list(
            self._session.scalars(
                select(DraftBiomarkerMeasurement)
                .options(joinedload(DraftBiomarkerMeasurement.biomarker))
                .where(
                    DraftBiomarkerMeasurement.lab_upload_id == upload_id,
                    DraftBiomarkerMeasurement.id.in_(ids),
                )
            )
        )

    def delete_for_upload(self, upload_id: uuid.UUID) -> None:
        """Delete an upload's draft rows; idempotent, for re-parse and after commit."""
        self._session.execute(
            delete(DraftBiomarkerMeasurement).where(
                DraftBiomarkerMeasurement.lab_upload_id == upload_id
            )
        )
