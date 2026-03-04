"""Add oauth_accounts and fix integration_tokens/user schema.

Revision ID: f4a6b7c8d9e0
Revises: e3f4a5b6c7d8
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f4a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users.hashed_password nullable for oauth users
    op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=True)

    # oauth_accounts
    op.create_table(
        "oauth_accounts",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_user_id", sa.String(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index(op.f("ix_oauth_accounts_user_id"), "oauth_accounts", ["user_id"], unique=False)

    # Fix integration_tokens schema (drop & recreate; early-stage project)
    op.drop_index(op.f("ix_integration_tokens_token"), table_name="integration_tokens")
    op.drop_table("integration_tokens")
    op.create_table(
        "integration_tokens",
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_integration_tokens_token"), "integration_tokens", ["token"], unique=True)
    op.create_index(op.f("ix_integration_tokens_user_id"), "integration_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_integration_tokens_user_id"), table_name="integration_tokens")
    op.drop_index(op.f("ix_integration_tokens_token"), table_name="integration_tokens")
    op.drop_table("integration_tokens")

    op.drop_index(op.f("ix_oauth_accounts_user_id"), table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=False)

