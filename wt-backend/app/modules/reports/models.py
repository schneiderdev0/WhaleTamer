from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class ReportStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class Report(BaseModel):
    __tablename__ = "reports"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("collector_events.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=ReportStatus.COMPLETED.value)
    model: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

