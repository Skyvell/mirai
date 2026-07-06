import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.models.base import Base


class User(Base):
    """A Mirai user, linked 1:1 to a Clerk identity.

    Deliberately minimal: identity and profile stay in Clerk; this row anchors
    the user's data in our own database. Created just-in-time by the auth
    dependency on the first authenticated request.
    """

    __tablename__ = "users"

    # UUIDv7 (time-ordered) generated client-side: Postgres 17 has no native
    # uuidv7(), and v4 fragments the primary-key index.
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    clerk_user_id: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
