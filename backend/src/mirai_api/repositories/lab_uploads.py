import uuid

from sqlalchemy import Row, delete, func, select
from sqlalchemy.orm import Session

from mirai_api.models import BiomarkerMeasurement, LabUpload


class LabUploadRepository:
    """Database access for lab uploads.

    Write methods flush but never commit; the owning service commits the
    session as the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_with_counts(self, user_id: uuid.UUID) -> list[Row]:
        """Return the user's uploads with their measurement counts, newest first."""
        count_sq = (
            select(func.count())
            .select_from(BiomarkerMeasurement)
            .where(BiomarkerMeasurement.lab_upload_id == LabUpload.id)
            .scalar_subquery()
        )
        return list(
            self._session.execute(
                select(
                    LabUpload.id,
                    LabUpload.filename,
                    LabUpload.status,
                    LabUpload.parsed_at,
                    LabUpload.created_at,
                    count_sq.label("measurement_count"),
                )
                .where(LabUpload.user_id == user_id)
                .order_by(LabUpload.created_at.desc())
            ).all()
        )

    def get_for_user(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUpload | None:
        """Return the user's upload with this id, or None."""
        return self._session.scalar(
            select(LabUpload).where(
                LabUpload.id == upload_id,
                LabUpload.user_id == user_id,
            )
        )

    def add(self, upload: LabUpload) -> None:
        """Stage a new upload row; the flush materializes its id."""
        self._session.add(upload)
        self._session.flush()

    def delete(self, upload: LabUpload) -> None:
        """Delete the upload row; measurements detach via the FK's ON DELETE SET NULL."""
        self._session.delete(upload)

    def delete_measurements(self, upload_id: uuid.UUID) -> None:
        """Hard-delete the measurements produced by this upload."""
        self._session.execute(
            delete(BiomarkerMeasurement).where(BiomarkerMeasurement.lab_upload_id == upload_id)
        )
