"""Revision notes on generation_history

Revision ID: 0014_generation_history_notes
Revises: 0013_generation_history_design_recipe
Create Date: 2026-10-21 00:00:00.000000

Adds ``generation_history.notes TEXT DEFAULT NULL`` — free-text revision notes
on a take (approvals, what changed, what to fix). Rows written before this
column stay NULL.

Additive + idempotent (guarded by PRAGMA table_info, matching 0013). The same
column is mirrored into ``core/db.py::_BASE_SCHEMA`` so fresh installs and
migrated DBs converge, and ``_reconcile_additive_columns`` heals DBs where
alembic cannot run.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_generation_history_notes"
down_revision: Union[str, None] = "0013_generation_history_design_recipe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    row = bind.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    if not _has_table("generation_history"):
        return
    if not _has_column("generation_history", "notes"):
        op.add_column(
            "generation_history",
            sa.Column("notes", sa.Text(), nullable=True, server_default=None),
        )


def downgrade() -> None:
    if _has_table("generation_history") and _has_column("generation_history", "notes"):
        op.drop_column("generation_history", "notes")
