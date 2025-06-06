from pydantic import BaseModel, EmailStr, field_validator, Field

from database.validators.accounts import validate_email, validate_password_strength


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr = Field(
        description="User email address. Must be valid and unique.",
        examples=["user@example.com"]
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be 8+ chars, include upper/lowercase, digit, special symbol.",
        examples=["Qwerty123!"]
    )

    model_config = {
        "from_attributes": True
    }

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return validate_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        return validate_password_strength(value)


class UserRegistrationRequestSchema(BaseEmailPasswordSchema):
    pass


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr
    is_active: bool = False
    message: str = "Account created. Please check your email to activate your account."

    model_config = {
        "from_attributes": True
    }
