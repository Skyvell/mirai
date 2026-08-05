from datetime import date

from sqlalchemy.orm import Session

from mirai_api.core.enums import Sex
from mirai_api.models import User


class UserRepository:
    """Database access for user rows.

    Write methods flush but never commit; the owning service commits the
    session as the transaction boundary.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def update_profile(self, user: User, *, sex: Sex, date_of_birth: date) -> None:
        user.sex = sex
        user.date_of_birth = date_of_birth
        self._session.flush()
