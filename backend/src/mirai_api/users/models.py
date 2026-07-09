import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.core.db import Base


class User(Base):
    """A Mirai user, linked 1:1 to a Clerk identity.

    Identity and profile stay in Clerk; this row anchors the user's data here.
    JIT-created by the auth dependency on the first authenticated request.
    """

    __tablename__ = "users"

    # Client-generated UUIDv7 (time-ordered); Postgres 17 has no native uuidv7().
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
    )
    clerk_user_id: Mapped[str] = mapped_column(
        Text,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
