import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.settings import s
from app.modules.auth.models import User
from app.modules.auth.oauth_models import OAuthAccount


GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_USER_URL = "https://api.github.com/user"
GITHUB_API_EMAILS_URL = "https://api.github.com/user/emails"

OAUTH_STATE_ALG = "HS256"


def _require_github_oauth_settings() -> None:
    if not s.github_client_id or not s.github_client_secret or not s.github_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured (GITHUB_CLIENT_ID/SECRET/REDIRECT_URI)",
        )


def build_github_authorize_url(scope: str = "read:user user:email repo") -> str:
    _require_github_oauth_settings()
    state = _create_state()
    params = {
        "client_id": s.github_client_id,
        "redirect_uri": s.github_redirect_uri,
        "scope": scope,
        "state": state,
    }
    return str(httpx.URL(GITHUB_OAUTH_AUTHORIZE_URL, params=params))


def _create_state() -> str:
    payload = {
        "nonce": secrets.token_urlsafe(16),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, s.jwt_secret_key, algorithm=OAUTH_STATE_ALG)


def verify_state(state: str) -> None:
    try:
        jwt.decode(state, s.jwt_secret_key, algorithms=[OAUTH_STATE_ALG])
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")


async def exchange_code_for_token(code: str, state: str) -> str:
    _require_github_oauth_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            GITHUB_OAUTH_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": s.github_client_id,
                "client_secret": s.github_client_secret,
                "code": code,
                "redirect_uri": s.github_redirect_uri,
                "state": state,
            },
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub token exchange failed: {resp.text}")
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="GitHub token exchange returned no access_token")
    return token


async def fetch_github_user(token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GITHUB_API_USER_URL,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub user fetch failed: {resp.text}")
    return resp.json()


async def fetch_primary_email(token: str) -> str | None:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GITHUB_API_EMAILS_URL,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
    if resp.status_code >= 400:
        return None
    emails = resp.json()
    if not isinstance(emails, list):
        return None
    for item in emails:
        if isinstance(item, dict) and item.get("primary") is True and item.get("verified") is True:
            email = item.get("email")
            if isinstance(email, str) and email:
                return email
    return None


async def fetch_user_repositories(token: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            params={"per_page": 100, "sort": "updated"},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub repositories fetch failed: {resp.text}")
    data = resp.json()
    if not isinstance(data, list):
        return []
    return data


async def fetch_repository_branches(token: str, full_name: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{full_name}/branches",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            params={"per_page": 100},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub branches fetch failed: {resp.text}")
    data = resp.json()
    if not isinstance(data, list):
        return []
    return data


async def fetch_repository_tree(token: str, full_name: str, branch: str) -> list[str]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{full_name}/git/trees/{branch}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            params={"recursive": "1"},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub tree fetch failed: {resp.text}")
    payload = resp.json()
    entries = payload.get("tree")
    if not isinstance(entries, list):
        return []
    paths: list[str] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "blob":
            continue
        path = item.get("path")
        if isinstance(path, str) and path:
            paths.append(path)
    return paths


async def fetch_repository_file_content(token: str, full_name: str, branch: str, path: str) -> str | None:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{full_name}/contents/{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            params={"ref": branch},
        )
    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub content read failed: {resp.text}")
    payload = resp.json()
    if not isinstance(payload, dict):
        return None
    if payload.get("encoding") != "base64":
        return None
    content = payload.get("content")
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        return base64.b64decode(content, validate=False).decode("utf-8")
    except Exception:
        return None


async def upsert_repository_file(
    token: str,
    full_name: str,
    branch: str,
    path: str,
    content: str,
    message: str,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=30) as client:
        get_resp = await client.get(
            f"https://api.github.com/repos/{full_name}/contents/{path}",
            headers=headers,
            params={"ref": branch},
        )
        sha: str | None = None
        if get_resp.status_code == 200:
            current = get_resp.json()
            if isinstance(current, dict):
                raw_sha = current.get("sha")
                if isinstance(raw_sha, str):
                    sha = raw_sha
        elif get_resp.status_code not in {404}:
            raise HTTPException(status_code=502, detail=f"GitHub content read failed: {get_resp.text}")

        body: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if sha:
            body["sha"] = sha

        put_resp = await client.put(
            f"https://api.github.com/repos/{full_name}/contents/{path}",
            headers=headers,
            json=body,
        )
    if put_resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"GitHub content update failed: {put_resp.text}")
    data = put_resp.json()
    return data if isinstance(data, dict) else {}


async def login_or_register_github_user(
    db: AsyncSession,
    github_user: dict[str, Any],
    access_token: str,
) -> dict[str, str]:
    provider = "github"
    provider_user_id = str(github_user.get("id"))
    login = github_user.get("login")
    email = github_user.get("email")
    if not email:
        email = await fetch_primary_email(access_token)
    if not email:
        email = f"github_{provider_user_id}@users.noreply.github.com"

    stmt = select(OAuthAccount).where(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_user_id == provider_user_id,
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account:
        stmt = select(User).where(User.id == account.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one()
    else:
        # ensure email uniqueness
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            user = existing
        else:
            user = User(email=email, hashed_password=None, auth_type="github")
            db.add(user)
            await db.commit()
            await db.refresh(user)

        account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            auth_metadata={
                "login": login,
                "access_token": access_token,
            },
        )
        db.add(account)
        await db.commit()

    jwt_token = create_access_token({"sub": user.email, "id": str(user.id)})
    return {"access_token": jwt_token, "token_type": "bearer"}
