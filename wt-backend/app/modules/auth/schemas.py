from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class EmailAuthDTO(BaseModel):
    email: EmailStr
    password: str


class EmailRegDTO(BaseModel):
    email: EmailStr
    password: str
    repassword: str


# CLI token (постоянный токен только для CLI, не JWT)
class CreateCLITokenDTO(BaseModel):
    name: str | None = None


class VerifyCLITokenDTO(BaseModel):
    token: str


class CLITokenCreateResponse(BaseModel):
    token: str  # показывается один раз при создании
    id: UUID
    name: str | None
    created_at: datetime


class CLITokenVerifyResponse(BaseModel):
    user_id: str
    email: str


class CLITokenListItem(BaseModel):
    id: UUID
    name: str | None
    token: str | None
    created_at: datetime


class GitHubStatusResponse(BaseModel):
    connected: bool


class GitHubRepositoryItem(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    default_branch: str


class GitHubBranchItem(BaseModel):
    name: str


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    auth_type: str
    github_connected: bool
