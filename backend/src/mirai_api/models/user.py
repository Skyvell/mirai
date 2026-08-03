import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.core.enums import Sex
from mirai_api.models.base import Base


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

    # Reference sex and birth date select which biomarker interval band applies;
    # null until the user sets them. values_callable stores the lowercase values.
    sex: Mapped[Sex | None] = mapped_column(
        Enum(
            Sex,
            name="sex",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
