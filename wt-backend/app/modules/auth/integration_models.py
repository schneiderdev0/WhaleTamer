from enum import Enum

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class IntegrationType(str, Enum):
    GITHUB = "github"
    DATA_COLLECTOR = "data_collector"
    TELEGRAM = "telegram"


class IntegrationToken(BaseModel):
    """Интеграционный токен/связка для внешних сервисов (GitHub, Data Collector, Telegram и т.п.)."""

    __tablename__ = "integration_tokens"

    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False, default=IntegrationType.DATA_COLLECTOR.value)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    int_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
