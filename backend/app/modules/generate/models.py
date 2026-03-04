from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class GenerateJobStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateJob(BaseModel):
    __tablename__ = "generate_jobs"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=GenerateJobStatus.PENDING.value)
    request: Mapped[dict] = mapped_column(JSONB, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    files: Mapped[list["GeneratedFile"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GeneratedFile(BaseModel):
    __tablename__ = "generated_files"

    job_id: Mapped[UUID] = mapped_column(ForeignKey("generate_jobs.id"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped[GenerateJob] = relationship(back_populates="files")

