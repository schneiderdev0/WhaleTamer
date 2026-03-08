import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.core.settings import s
from app.modules.auth.dependencies import get_current_user_from_bearer
from app.modules.auth.models import User
from app.modules.auth.oauth_models import OAuthAccount
from app.modules.auth.schemas import (
    CLITokenCreateResponse,
    CLITokenListItem,
    CLITokenVerifyResponse,
    CreateCLITokenDTO,
    EmailAuthDTO,
    EmailRegDTO,
    GitHubRepositoryItem,
    GitHubStatusResponse,
    UserProfileResponse,
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
            f"{s.frontend_base_url.rstrip('/')}/login"
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


@router.get("/me", response_model=UserProfileResponse, summary="Current user profile")
async def me(
    payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    github_stmt = (
        select(OAuthAccount)
        .where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "github")
        .limit(1)
    )
    github_result = await db.execute(github_stmt)
    github_account = github_result.scalar_one_or_none()
    return UserProfileResponse(
        user_id=str(user.id),
        email=user.email,
        auth_type=user.auth_type,
        github_connected=bool(github_account),
    )


@router.get("/github/status", response_model=GitHubStatusResponse, summary="GitHub connection status")
async def github_status(
    payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    stmt = (
        select(OAuthAccount)
        .where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "github")
        .order_by(OAuthAccount.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    return GitHubStatusResponse(connected=bool(account))


@router.get("/github/repositories", response_model=list[GitHubRepositoryItem], summary="List GitHub repositories")
async def github_repositories(
    payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    stmt = (
        select(OAuthAccount)
        .where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "github")
        .order_by(OAuthAccount.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub is not connected")

    access_token = (account.auth_metadata or {}).get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub access token is missing")

    repos = await github_oauth.fetch_user_repositories(access_token)
    items: list[GitHubRepositoryItem] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        repo_id = repo.get("id")
        if not isinstance(repo_id, int):
            continue
        items.append(
            GitHubRepositoryItem(
                id=repo_id,
                name=str(repo.get("name") or ""),
                full_name=str(repo.get("full_name") or ""),
                private=bool(repo.get("private")),
                html_url=str(repo.get("html_url") or ""),
                default_branch=str(repo.get("default_branch") or "main"),
            )
        )
    return items


@router.delete("/github/unlink", summary="Unlink GitHub account")
async def github_unlink(
    payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == user_id,
        OAuthAccount.provider == "github",
    )
    result = await db.execute(stmt)
    accounts = list(result.scalars().all())
    if not accounts:
        return {"status": "ok", "unlinked": False}

    for account in accounts:
        await db.delete(account)
    await db.commit()
    return {"status": "ok", "unlinked": True}


# CLI token API (постоянный токен только для CLI)
@router.post("/cli-tokens", response_model=CLITokenCreateResponse, summary="Create CLI token")
async def create_cli_token(
    dto: CreateCLITokenDTO | None = Body(None),
    payload: dict = Depends(get_current_user_from_bearer),
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
    payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    tokens = await cli_tokens_service.list_cli_tokens(user_id, db)
    return [
        CLITokenListItem(id=t.id, name=t.name, token=t.plain_token, created_at=t.created_at)
        for t in tokens
    ]


@router.delete("/cli-tokens/{token_id}", summary="Delete CLI token")
async def delete_cli_token(
    token_id: str,
    payload: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(payload["id"])
    try:
        token_uuid = uuid.UUID(token_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token_id")

    deleted = await cli_tokens_service.delete_cli_token(user_id=user_id, token_id=token_uuid, db=db)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CLI token not found")
    return {"status": "ok", "deleted": True}
