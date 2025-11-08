from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    username: str = Field(..., description="Unique username for the user")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=1, description="User password")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    username: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(..., description="Whether the user account is active")


class LogoutResponse(BaseModel):
    message: str = Field(..., description="Logout confirmation message")

