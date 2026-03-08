from datetime import datetime

from pydantic import BaseModel, Field


class TelegramLinkTokenResponse(BaseModel):
    token: str  # показываем один раз


class TelegramConfirmLinkRequest(BaseModel):
    token: str = Field(..., description="Telegram link token (tg_...)")
    chat_id: int
    username: str | None = None


class TelegramConfirmLinkResponse(BaseModel):
    status: str = "linked"


class TelegramLinkedInfo(BaseModel):
    linked: bool
    chat_id: int | None = None
    username: str | None = None


class TelegramLatestReportResponse(BaseModel):
    report_id: str
    created_at: datetime
    status: str
    model: str
    summary: str
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class TelegramNotificationSettings(BaseModel):
    enabled: bool = True
    frequency: str = Field(default="event", pattern="^(event|hourly|daily)$")
    severity: str = Field(default="all", pattern="^(all|critical)$")


class TelegramNotificationSettingsUpdate(BaseModel):
    enabled: bool | None = None
    frequency: str | None = Field(default=None, pattern="^(event|hourly|daily)$")
    severity: str | None = Field(default=None, pattern="^(all|critical)$")


class TelegramNotificationSettingsResponse(BaseModel):
    linked: bool
    chat_id: int | None = None
    username: str | None = None
    settings: TelegramNotificationSettings
