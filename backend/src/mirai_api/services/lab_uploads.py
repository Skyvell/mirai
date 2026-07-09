import uuid
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from mirai_api.core.enums import UploadStatus
from mirai_api.models import BiomarkerMeasurement, LabUpload
from mirai_api.services import storage
from mirai_api.services.lab_parsing import MappedMeasurement


def store_upload(session: Session, user_id: uuid.UUID, filename: str, data: bytes) -> LabUpload:
    """Write the PDF to GCS, then record the upload row. Blocking."""
    upload = LabUpload(
        id=uuid.uuid7(),
        user_id=user_id,
        filename=filename,
        status=UploadStatus.UPLOADED,
    )
    storage.upload(
        upload.gcs_object_name,
        data,
        "application/pdf",
    )
    session.add(upload)
    session.commit()
    return upload


def persist_results(
    session: Session,
    upload: LabUpload,
    mapped: list[MappedMeasurement],
    measured_at: date | None,
) -> None:
    """Insert measurements and mark the upload parsed. Blocking."""
    session.add_all(
        BiomarkerMeasurement(
            user_id=upload.user_id,
            biomarker_id=m.biomarker.id,
            lab_upload_id=upload.id,
            value=m.measurement.value,
            unit=m.measurement.unit,
            reference_low=m.measurement.reference_low,
            reference_high=m.measurement.reference_high,
            measured_at=measured_at,
        )
        for m in mapped
    )
    upload.status = UploadStatus.PARSED
    upload.parsed_at = datetime.now(UTC)
    session.commit()
