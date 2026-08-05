from sqlalchemy.orm import Session

from mirai_api.models import User
from mirai_api.repositories.users import UserRepository
from mirai_api.schemas.me import MeResponse, MeUpdate


class UserService:
    """Application logic for the user profile; owns the transaction boundary."""

    def __init__(self, user_repository: UserRepository, session: Session) -> None:
        self._user_repository = user_repository

        # Used for transaction control only; queries go through the repository.
        self._session = session

    def get_profile(self, user: User) -> MeResponse:
        return _to_me_response(user)

    def update_profile(self, user: User, update: MeUpdate) -> MeResponse:
        self._user_repository.update_profile(
            user,
            sex=update.sex,
            date_of_birth=update.date_of_birth,
        )
        self._session.commit()
        return _to_me_response(user)


def _to_me_response(user: User) -> MeResponse:
    return MeResponse(
        user_id=user.id,
        clerk_user_id=user.clerk_user_id,
        sex=user.sex,
        date_of_birth=user.date_of_birth,
    )
