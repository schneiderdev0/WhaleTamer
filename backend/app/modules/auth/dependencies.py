"""Зависимости для auth: приём и JWT, и CLI-токена в Bearer."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.auth.services import cli_tokens as cli_tokens_service

security_scheme = HTTPBearer(auto_error=True)


async def get_current_user_from_bearer(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Принимает Bearer: либо JWT (сайт), либо CLI-токен (wt_...).
    Возвращает {"id": str(user_id), "sub": email}.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )
    if token.startswith("wt_"):
        user = await cli_tokens_service.verify_cli_token(token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired CLI token",
            )
        return {"id": str(user.id), "sub": user.email}
    # JWT
    payload = decode_access_token(token)
    return {"id": payload.get("id"), "sub": payload.get("sub")}
