import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.core.db import Base
from mirai_api.core.enums import UploadStatus


class LabUpload(Base):
    """One uploaded lab PDF and its parse lifecycle.

    The stored object lives at ``gcs_object_name``; a failed parse keeps the
    row and the object for debugging.
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
    # values_callable stores the lowercase values, not the member names.
    status: Mapped[UploadStatus] = mapped_column(
        Enum(
            UploadStatus,
            name="lab_upload_status",
            native_enum=False,
            values_callable=lambda e: [m.value for m in e],
        ),
    )
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    @property
    def gcs_object_name(self) -> str:
        """Deterministic object path: user-first prefix, upload id as the stem."""
        return f"users/{self.user_id}/labs/{self.id}.pdf"
