from sqlalchemy.orm import Session

from mirai_api.models import User
from mirai_api.repositories.user import UserRepository
from mirai_api.schemas.me import MeUpdate


class UserService:
    """Application logic for the user profile; owns the transaction boundary."""

    def __init__(self, user_repository: UserRepository, session: Session) -> None:
        self._user_repository = user_repository

        # Used for transaction control only; queries go through the repository.
        self._session = session

    def update_profile(self, user: User, update: MeUpdate) -> User:
        self._user_repository.update_profile(
            user,
            sex=update.sex,
            date_of_birth=update.date_of_birth,
        )
        self._session.commit()
        return user
