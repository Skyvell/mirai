from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from mirai_api.core.enums import Sex
from mirai_api.models import User


class UserRepository:
    """Database access for user rows.

    Write methods flush but never commit; the request's session dependency
    owns the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_user(self, clerk_user_id: str) -> User | None:
        """Resolve a Clerk identity to its local row."""
        return self._session.scalar(select(User).where(User.clerk_user_id == clerk_user_id))

    def update_profile(self, user: User, *, sex: Sex, date_of_birth: date) -> None:
        user.sex = sex
        user.date_of_birth = date_of_birth
        self._session.flush()
