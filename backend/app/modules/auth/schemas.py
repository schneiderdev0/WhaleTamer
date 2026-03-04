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
    created_at: datetime
