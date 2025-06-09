from pydantic import BaseModel, EmailStr, field_validator, Field, model_validator

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
    password_confirm: str = Field(
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

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match.")
        return self


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


class EmailRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="User email address.")

    model_config = {
        "from_attributes": True
    }


class UserLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequestSchema(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    new_password_repeat: str = Field(..., min_length=8)


    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        return validate_password_strength(value)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.new_password_repeat:
            raise ValueError("New passwords do not match.")
        return self
