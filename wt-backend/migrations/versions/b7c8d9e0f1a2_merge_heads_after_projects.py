"""Merge parallel alembic heads.

Revision ID: b7c8d9e0f1a2
Revises: 0b1c2d3e4f50, a1b2c3d4e5f6
Create Date: 2026-03-08
"""

from typing import Sequence, Union


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = ("0b1c2d3e4f50", "a1b2c3d4e5f6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
