import uuid
from datetime import UTC, date, datetime
from typing import Self

from pydantic import BaseModel, model_validator

from mirai_api.core.enums import Sex
from mirai_api.models import User


class MeResponse(BaseModel):
    user_id: uuid.UUID
    clerk_user_id: str
    sex: Sex | None
    date_of_birth: date | None

    @classmethod
    def from_user(cls, user: User) -> MeResponse:
        return cls(
            user_id=user.id,
            clerk_user_id=user.clerk_user_id,
            sex=user.sex,
            date_of_birth=user.date_of_birth,
        )


class MeUpdate(BaseModel):
    sex: Sex
    date_of_birth: date

    @model_validator(mode="after")
    def _reject_future_birth_date(self) -> Self:
        if self.date_of_birth > datetime.now(UTC).date():
            raise ValueError("date_of_birth cannot be in the future.")

        return self
