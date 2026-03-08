from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class OAuthAccount(BaseModel):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String, nullable=False)
    # DB column is named "metadata" in existing migrations; map it to a safe Python attribute.
    auth_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
