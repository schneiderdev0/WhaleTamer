import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import s
from app.core.security import get_current_user_payload
from app.modules.auth.schemas import (
    CLITokenCreateResponse,
    CLITokenListItem,
    CLITokenVerifyResponse,
    CreateCLITokenDTO,
    EmailAuthDTO,
    EmailRegDTO,
    VerifyCLITokenDTO,
)
from app.modules.auth.services import cli_tokens as cli_tokens_service
from app.modules.auth.services import email_auth
from app.modules.auth.services import github_oauth

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", summary="Register new user")
async def register(dto: EmailRegDTO, db: AsyncSession = Depends(get_db)):
    return await email_auth.register(dto, db)


@router.post("/login", summary="Login user")
async def login(dto: EmailAuthDTO, db: AsyncSession = Depends(get_db)):
    return await email_auth.auth(dto, db)


@router.get("/github/login", summary="Get GitHub OAuth authorize URL")
async def github_login():
    url = github_oauth.build_github_authorize_url()
    return {"url": url}


@router.get("/github/callback", summary="GitHub OAuth callback (exchanges code, returns JWT)")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    github_oauth.verify_state(state)
    token = await github_oauth.exchange_code_for_token(code=code, state=state)
    user = await github_oauth.fetch_github_user(token)
    auth = await github_oauth.login_or_register_github_user(db=db, github_user=user, access_token=token)

    # If frontend_base_url is configured, redirect back to frontend with token in query.
    if s.frontend_base_url:
        target = (
            f"{s.frontend_base_url.rstrip('/')}/auth"
            f"?token={auth['access_token']}"
            f"&user_id={user.get('id')}"
            f"&email={user.get('email') or ''}"
        )
        return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)

    # Fallback: return JWT as JSON (for CLI tools, tests, etc.)
    return auth


@router.get("/verify", summary="Verify JWT (Bearer)")
async def verify_jwt(payload: dict = Depends(get_current_user_payload)):
    return {"user_id": payload.get("id"), "email": payload.get("sub")}


# CLI token API (постоянный токен только для CLI)
@router.post("/cli-tokens", response_model=CLITokenCreateResponse, summary="Create CLI token")
async def create_cli_token(
    dto: CreateCLITokenDTO | None = Body(None),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    name = dto.name if dto else None
    plain, record = await cli_tokens_service.create_cli_token(user_id, name, db)
    return CLITokenCreateResponse(
        token=plain,
        id=record.id,
        name=record.name,
        created_at=record.created_at,
    )


@router.post("/cli-tokens/verify", response_model=CLITokenVerifyResponse, summary="Verify CLI token")
async def verify_cli_token(
    dto: VerifyCLITokenDTO,
    db: AsyncSession = Depends(get_db),
):
    user = await cli_tokens_service.verify_cli_token(dto.token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired CLI token",
        )
    return CLITokenVerifyResponse(user_id=str(user.id), email=user.email)


@router.get("/cli-tokens", response_model=list[CLITokenListItem], summary="List user CLI tokens")
async def list_cli_tokens(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    tokens = await cli_tokens_service.list_cli_tokens(user_id, db)
    return [
        CLITokenListItem(id=t.id, name=t.name, created_at=t.created_at)
        for t in tokens
    ]
