"""Merge the take revision-notes branch into the main migration line

Revision ID: 0018_merge_history_notes
Revises: 0017_job_events_unique_seq, 0014_generation_history_notes
Create Date: 2026-10-29 00:00:00.000000

``0014_generation_history_notes`` (this fork) and ``0014_cloud_sync`` (the
original project) both branched from 0013. Both stay unchanged so every
existing database keeps a known revision: one stamped at either branch
upgrades through the other and lands here. No schema change of its own.
"""
from typing import Sequence, Union


revision: str = "0018_merge_history_notes"
down_revision: Union[str, Sequence[str], None] = (
    "0017_job_events_unique_seq",
    "0014_generation_history_notes",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
