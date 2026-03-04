import hashlib
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.integration_models import IntegrationToken, IntegrationType
from app.modules.auth.models import User


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _make_plain(prefix: str) -> str:
    return f"{prefix}{secrets.token_urlsafe(32)}"


async def create_integration_token(
    user_id: uuid.UUID,
    type_: IntegrationType,
    db: AsyncSession,
    status: str = "active",
    metadata: dict | None = None,
) -> tuple[str, IntegrationToken]:
    """Создаёт интеграционный токен, сохраняет хэш в БД, возвращает (plain_token, record)."""
    prefix = "dc_" if type_ == IntegrationType.DATA_COLLECTOR else "tg_"
    plain = _make_plain(prefix)
    token_hash = _hash_token(plain)
    record = IntegrationToken(
        user_id=user_id,
        token=token_hash,
        type=type_.value,
        status=status,
        metadata=metadata or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return plain, record


async def verify_integration_token(
    token: str,
    allowed_types: set[IntegrationType],
    db: AsyncSession,
) -> User | None:
    if not token or not token.strip():
        return None
    token_hash = _hash_token(token.strip())
    stmt = select(IntegrationToken).where(
        IntegrationToken.token == token_hash,
        IntegrationToken.status == "active",
        IntegrationToken.type.in_([t.value for t in allowed_types]),
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if not record:
        return None
    stmt = select(User).where(User.id == record.user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_integration_token_record(
    token: str,
    allowed_types: set[IntegrationType],
    db: AsyncSession,
) -> IntegrationToken | None:
    if not token or not token.strip():
        return None
    token_hash = _hash_token(token.strip())
    stmt = select(IntegrationToken).where(
        IntegrationToken.token == token_hash,
        IntegrationToken.status == "active",
        IntegrationToken.type.in_([t.value for t in allowed_types]),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

