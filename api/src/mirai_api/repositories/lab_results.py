import uuid
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from mirai_api.models import LabResult


class LabResultRepository:
    """Database access for lab results awaiting review.

    Write methods flush but never commit; LabUploadService owns the
    transaction boundary for the parse saga.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_all(self, results: list[LabResult]) -> None:
        """Stage new result rows; the flush materializes their ids."""
        self._session.add_all(results)
        self._session.flush()

    def list_for_upload(self, upload_id: uuid.UUID) -> list[LabResult]:
        """Return an upload's result rows, biomarker eager-loaded, in insertion order."""
        return list(
            self._session.scalars(
                select(LabResult)
                .options(joinedload(LabResult.biomarker))
                .where(LabResult.lab_upload_id == upload_id)
                .order_by(LabResult.id)
            )
        )

    def get_for_upload(
        self,
        upload_id: uuid.UUID,
        ids: Iterable[uuid.UUID],
    ) -> list[LabResult]:
        """Return an upload's result rows matching the given ids, biomarker eager-loaded."""
        return list(
            self._session.scalars(
                select(LabResult)
                .options(joinedload(LabResult.biomarker))
                .where(
                    LabResult.lab_upload_id == upload_id,
                    LabResult.id.in_(ids),
                )
            )
        )

    def delete_for_upload(self, upload_id: uuid.UUID) -> None:
        """Delete an upload's result rows; idempotent, for re-parse and after commit."""
        self._session.execute(delete(LabResult).where(LabResult.lab_upload_id == upload_id))
