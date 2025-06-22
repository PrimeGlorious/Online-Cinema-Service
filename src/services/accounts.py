from database import UserModel
from database.validators import accounts as validators
from security.passwords import hash_password, verify_password as check_password


class UserService:
    @staticmethod
    def create(email: str, raw_password: str, group_id: int) -> UserModel:
        """
        Create a new user, hash password, validate email and password.
        """
        # Validate email and password BEFORE creating user
        valid_email = UserService.validate_email(email)
        validators.validate_password_strength(raw_password)

        user = UserModel(email=valid_email, group_id=group_id)
        UserService.set_password(user, raw_password)
        return user

    @staticmethod
    def set_password(user: UserModel, raw_password: str) -> None:
        """
        Hash and set password for the user.
        """
        validators.validate_password_strength(raw_password)
        user._hashed_password = hash_password(raw_password)

    @staticmethod
    def verify_password(user: UserModel, raw_password: str) -> bool:
        """
        Check if the given raw password matches the stored hashed password.
        """
        return check_password(raw_password, user._hashed_password)

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate user email.
        """
        return validators.validate_email(email.lower())
