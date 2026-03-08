from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user_from_bearer
from app.modules.reports.models import Report, ReportStatus
from app.modules.reports.schemas import (
    ReportCreateRequest,
    ReportListItem,
    ReportResponse,
)
from app.modules.reports.service import generate_report_for_event

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, summary="Generate report for collector event")
async def create_report(
    body: ReportCreateRequest,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    try:
        event_id = UUID(body.event_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event_id")

    data, raw, model = await generate_report_for_event(db=db, user_id=user_id, event_id=event_id)

    report = Report(
        user_id=user_id,
        event_id=event_id,
        status=ReportStatus.COMPLETED.value,
        model=model,
        content=data,
        raw_text=raw,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportResponse(
        id=str(report.id),
        event_id=str(report.event_id),
        status=report.status,
        model=report.model,
        content=report.content,  # pydantic will coerce into ReportContent
        error=report.error,
        created_at=report.created_at,
    )


@router.get("", response_model=list[ReportListItem], summary="List reports")
async def list_reports(
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    stmt = select(Report).where(Report.user_id == user_id).order_by(Report.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    reports = list(result.scalars().all())
    return [
        ReportListItem(
            id=str(r.id),
            event_id=str(r.event_id),
            status=r.status,
            model=r.model,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=ReportResponse, summary="Get report by id")
async def get_report(
    report_id: str,
    user: dict = Depends(get_current_user_from_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id = UUID(user["id"])
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report_id")

    stmt = select(Report).where(Report.id == report_uuid, Report.user_id == user_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return ReportResponse(
        id=str(report.id),
        event_id=str(report.event_id),
        status=report.status,
        model=report.model,
        content=report.content if report.status == ReportStatus.COMPLETED.value else None,
        error=report.error,
        created_at=report.created_at,
    )

