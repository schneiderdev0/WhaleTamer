from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportCreateRequest(BaseModel):
    event_id: str = Field(..., description="collector_events.id")


class ReportContent(BaseModel):
    summary: str
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    observations: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    id: str
    event_id: str
    status: str
    model: str
    content: ReportContent | None = None
    error: str | None = None
    created_at: datetime


class ReportListItem(BaseModel):
    id: str
    event_id: str
    status: str
    model: str
    created_at: datetime

