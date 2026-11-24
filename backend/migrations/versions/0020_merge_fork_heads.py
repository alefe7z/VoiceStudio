"""Merge the fork's notes line with the original project's newer migrations

Revision ID: 0020_merge_fork_heads
Revises: 0019_list_sort_indexes, 0018_merge_history_notes
Create Date: 2026-11-24 00:00:00.000000

``0018_merge_history_notes`` (this fork) and ``0018_pronunciation_profile_scope``
→ ``0019_list_sort_indexes`` (the original project) both follow 0017. Both stay
unchanged so a database stamped at either head upgrades through the other and
lands here. No schema change of its own.
"""
from typing import Sequence, Union


revision: str = "0020_merge_fork_heads"
down_revision: Union[str, Sequence[str], None] = (
    "0019_list_sort_indexes",
    "0018_merge_history_notes",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
