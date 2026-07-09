import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.models.base import Base


class LabUpload(Base):
    """One uploaded lab PDF and its parse lifecycle.

    The stored object lives at the derived ``gcs_object_name``; only the
    original filename is persisted here. A failed parse keeps the row and the
    object for debugging.
    """

    __tablename__ = "lab_uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("uploaded", "parsed", "failed", name="lab_upload_status", native_enum=False)
    )
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def gcs_object_name(self) -> str:
        """Deterministic object path: user-first prefix, upload id as the stem."""
        return f"users/{self.user_id}/labs/{self.id}.pdf"
