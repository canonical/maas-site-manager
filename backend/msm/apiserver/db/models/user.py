from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class User(BaseModel):
    """A user."""

    id: int
    email: EmailStr = Field(title="email@example.com")
    username: str
    full_name: str
    is_admin: bool
    provider_id: int | None = None
    auth_id: UUID


class Worker(BaseModel):
    """A temporal worker."""

    auth_id: UUID
    is_admin: bool = True


class UserCreate(BaseModel):
    """Creating a new user"""

    email: EmailStr
    username: str
    full_name: str
    password: str
    is_admin: bool
    provider_id: int | None = None


class UserUpdate(BaseModel):
    """User updatable fields"""

    username: str | None = None
    full_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    is_admin: bool | None = None
