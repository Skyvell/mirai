import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.core.enums import UploadStatus
from mirai_api.models.base import Base


class LabUpload(Base):
    """One uploaded lab PDF and its parse lifecycle.

    The stored object lives at ``gcs_object_name``; a failed parse keeps the
    row and the object for debugging. Extracted values land as draft rows the
    user reviews before they are committed to the biomarker record.
    """

    __tablename__ = "lab_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    filename: Mapped[str] = mapped_column(Text)
    # SHA-256 of the PDF bytes; blocks re-uploads of the byte-identical file.
    content_sha256: Mapped[str | None] = mapped_column(Text, index=True)
    # values_callable stores the lowercase values, not the member names.
    status: Mapped[UploadStatus] = mapped_column(
        Enum(
            UploadStatus,
            name="lab_upload_status",
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
    )
    # Report collection date; parsed from the PDF, user-confirmable, copied to
    # each measurement on commit.
    measured_at: Mapped[date | None] = mapped_column(Date)
    # Human-readable reason set when status is failed.
    error_message: Mapped[str | None] = mapped_column(Text)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    @property
    def gcs_object_name(self) -> str:
        """Deterministic object path: user-first prefix, upload id as the stem."""
        return f"users/{self.user_id}/labs/{self.id}.pdf"
