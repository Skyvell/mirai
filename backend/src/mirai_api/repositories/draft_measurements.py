import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from mirai_api.models import DraftMeasurement


class DraftMeasurementRepository:
    """Database access for draft measurements awaiting review.

    Write methods flush but never commit; the owning service commits the
    session as the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_all(self, drafts: list[DraftMeasurement]) -> None:
        """Stage new draft rows; the flush materializes their ids."""
        self._session.add_all(drafts)
        self._session.flush()

    def list_for_upload(self, upload_id: uuid.UUID) -> list[DraftMeasurement]:
        """Return an upload's draft rows, biomarker eager-loaded, in insertion order."""
        return list(
            self._session.scalars(
                select(DraftMeasurement)
                .options(joinedload(DraftMeasurement.biomarker))
                .where(DraftMeasurement.lab_upload_id == upload_id)
                .order_by(DraftMeasurement.id)
            )
        )

    def delete_for_upload(self, upload_id: uuid.UUID) -> None:
        """Delete an upload's draft rows; idempotent, for re-parse and after commit."""
        self._session.execute(
            delete(DraftMeasurement).where(DraftMeasurement.lab_upload_id == upload_id)
        )
