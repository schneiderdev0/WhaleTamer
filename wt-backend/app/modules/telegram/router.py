from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.modules.auth.integration_models import IntegrationToken, IntegrationType
from app.modules.auth.services import integration_tokens as integration_tokens_service
from app.modules.auth.dependencies import get_current_user_from_bearer
from app.modules.reports.models import Report
from app.modules.telegram.schemas import (
    TelegramConfirmLinkRequest,
    TelegramConfirmLinkResponse,
    TelegramLatestReportResponse,
    TelegramLinkTokenResponse,
    TelegramLinkedInfo,
    TelegramNotificationSettings,
    TelegramNotificationSettingsResponse,
    TelegramNotificationSettingsUpdate,
)

router = APIRouter(prefix="/telegram", tags=["Telegram"])


def _default_notify_settings() -> dict:
    return {"enabled": True, "frequency": "event", "severity": "all"}


def _normalize_notify_settings(metadata: dict | None) -> dict:
    md = metadata or {}
    raw = md.get("notify_settings")
    if not isinstance(raw, dict):
        return _default_notify_settings()

    enabled = bool(raw.get("enabled", True))
    frequency = str(raw.get("frequency", "event"))
    severity = str(raw.get("severity", "all"))

    if frequency not in {"event", "hourly", "daily"}:
        frequency = "event"
    if severity not in {"all", "critical"}:
        severity = "all"

    return {"enabled": enabled, "frequency": frequency, "severity": severity}


@router.post("/link-token", response_model=TelegramLinkTokenResponse, summary="Create Telegram link token")
async def create_link_token(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(payload["id"])
    plain, _record = await integration_tokens_service.create_integration_token(
        user_id=user_id,
        type_=IntegrationType.TELEGRAM,
        status="active",
        metadata={},
        db=db,
    )
    return TelegramLinkTokenResponse(token=plain)


@router.post("/link", response_model=TelegramConfirmLinkResponse, summary="Confirm Telegram link (called by bot)")
async def confirm_link(
    body: TelegramConfirmLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    record = await integration_tokens_service.get_integration_token_record(
        token=body.token,
        allowed_types={IntegrationType.TELEGRAM},
        db=db,
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    record.metadata = {
        **(record.metadata or {}),
        "chat_id": body.chat_id,
        "username": body.username,
    }
    db.add(record)
    await db.commit()
    return TelegramConfirmLinkResponse()


@router.get("/me", response_model=TelegramLinkedInfo, summary="Get Telegram link status (by JWT)")
async def get_link_status(
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = (
        select(IntegrationToken)
        .where(IntegrationToken.user_id == user_id, IntegrationToken.type == IntegrationType.TELEGRAM.value)
        .order_by(IntegrationToken.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if not token:
        return TelegramLinkedInfo(linked=False)
    chat_id = (token.metadata or {}).get("chat_id")
    username = (token.metadata or {}).get("username")
    return TelegramLinkedInfo(linked=bool(chat_id), chat_id=chat_id, username=username)


@router.get(
    "/notification-settings",
    response_model=TelegramNotificationSettingsResponse,
    summary="Get Telegram notification settings",
)
async def get_notification_settings(
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = (
        select(IntegrationToken)
        .where(IntegrationToken.user_id == user_id, IntegrationToken.type == IntegrationType.TELEGRAM.value)
        .order_by(IntegrationToken.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if not token:
        return TelegramNotificationSettingsResponse(
            linked=False,
            settings=TelegramNotificationSettings(**_default_notify_settings()),
        )
    chat_id = (token.metadata or {}).get("chat_id")
    username = (token.metadata or {}).get("username")
    return TelegramNotificationSettingsResponse(
        linked=bool(chat_id),
        chat_id=chat_id,
        username=username,
        settings=TelegramNotificationSettings(**_normalize_notify_settings(token.metadata)),
    )


@router.put(
    "/notification-settings",
    response_model=TelegramNotificationSettingsResponse,
    summary="Update Telegram notification settings",
)
async def update_notification_settings(
    body: TelegramNotificationSettingsUpdate,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = (
        select(IntegrationToken)
        .where(IntegrationToken.user_id == user_id, IntegrationToken.type == IntegrationType.TELEGRAM.value)
        .order_by(IntegrationToken.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telegram integration is not linked")

    settings = _normalize_notify_settings(token.metadata)
    payload = body.model_dump(exclude_none=True)
    settings.update(payload)

    token.metadata = {
        **(token.metadata or {}),
        "notify_settings": settings,
    }
    db.add(token)
    await db.commit()

    chat_id = (token.metadata or {}).get("chat_id")
    username = (token.metadata or {}).get("username")
    return TelegramNotificationSettingsResponse(
        linked=bool(chat_id),
        chat_id=chat_id,
        username=username,
        settings=TelegramNotificationSettings(**settings),
    )


@router.get(
    "/reports/latest",
    response_model=TelegramLatestReportResponse,
    summary="Get latest report (Telegram token auth)",
)
async def latest_report(
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = select(Report).where(Report.user_id == user_id).order_by(Report.created_at.desc()).limit(1)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reports")
    summary = ""
    issues: list[str] = []
    recommendations: list[str] = []
    if isinstance(report.content, dict):
        summary = str(report.content.get("summary") or "")
        issues_raw = report.content.get("issues")
        if isinstance(issues_raw, list):
            issues = [str(x) for x in issues_raw if x is not None]
        recs_raw = report.content.get("recommendations")
        if isinstance(recs_raw, list):
            recommendations = [str(x) for x in recs_raw if x is not None]
    return TelegramLatestReportResponse(
        report_id=str(report.id),
        created_at=report.created_at,
        status=report.status,
        model=report.model,
        summary=summary,
        issues=issues,
        recommendations=recommendations,
    )
