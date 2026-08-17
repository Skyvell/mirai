from mirai_api.models import User
from mirai_api.repositories.users import UserRepository
from mirai_api.schemas.me import MeResponse, MeUpdate


class UserService:
    """Application logic for the user profile; the request owns the transaction."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def update_profile(self, user: User, update: MeUpdate) -> MeResponse:
        self._user_repository.update_profile(
            user,
            sex=update.sex,
            date_of_birth=update.date_of_birth,
        )
        return MeResponse.from_user(user)
