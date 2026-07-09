import uuid

from pydantic import BaseModel


class MeResponse(BaseModel):
    user_id: uuid.UUID
    clerk_user_id: str
