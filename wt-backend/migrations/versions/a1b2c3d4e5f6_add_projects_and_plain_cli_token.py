"""Add projects table and plain_token for cli_tokens.

Revision ID: a1b2c3d4e5f6
Revises: f4a6b7c8d9e0
Create Date: 2026-03-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f4a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cli_tokens", sa.Column("plain_token", sa.String(), nullable=True))

    op.create_table(
        "projects",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("github_repo_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("html_url", sa.String(), nullable=False),
        sa.Column("default_branch", sa.String(), nullable=False, server_default="main"),
        sa.Column("selected_branch", sa.String(), nullable=False, server_default="main"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)
    op.create_index(op.f("ix_projects_github_repo_id"), "projects", ["github_repo_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_github_repo_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_column("cli_tokens", "plain_token")
