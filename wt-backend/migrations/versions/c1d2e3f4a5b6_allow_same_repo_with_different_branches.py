"""Allow linking the same repository on different branches.

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-03-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_projects_user_repo_branch",
        "projects",
        ["user_id", "github_repo_id", "selected_branch"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_projects_user_repo_branch", "projects", type_="unique")
