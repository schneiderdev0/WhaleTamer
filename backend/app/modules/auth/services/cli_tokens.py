import hashlib
import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import CLIToken, User


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_cli_token(
    user_id: uuid.UUID,
    name: str | None,
    db: AsyncSession,
) -> tuple[str, CLIToken]:
    """Создаёт CLI-токен, сохраняет хэш в БД, возвращает (plain_token, record)."""
    plain = f"wt_{secrets.token_urlsafe(32)}"
    token_hash = _hash_token(plain)
    record = CLIToken(user_id=user_id, token_hash=token_hash, name=name)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return plain, record


async def verify_cli_token(token: str, db: AsyncSession) -> User | None:
    """Проверяет токен по телу запроса. Возвращает User или None."""
    if not token or not token.strip():
        return None
    token_hash = _hash_token(token.strip())
    stmt = select(CLIToken).where(CLIToken.token_hash == token_hash)
    result = await db.execute(stmt)
    cli_token = result.scalar_one_or_none()
    if not cli_token:
        return None
    stmt = select(User).where(User.id == cli_token.user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_cli_tokens(user_id: uuid.UUID, db: AsyncSession) -> list[CLIToken]:
    """Список CLI-токенов пользователя (без самого токена)."""
    stmt = select(CLIToken).where(CLIToken.user_id == user_id).order_by(CLIToken.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
