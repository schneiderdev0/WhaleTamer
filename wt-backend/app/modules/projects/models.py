from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class Project(BaseModel):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("user_id", "github_repo_id", "selected_branch", name="uq_projects_user_repo_branch"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    github_repo_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    html_url: Mapped[str] = mapped_column(String, nullable=False)
    default_branch: Mapped[str] = mapped_column(String, nullable=False, default="main")
    selected_branch: Mapped[str] = mapped_column(String, nullable=False, default="main")
