"""Delivery preflight for a dub job.

Checks a finished dub before it leaves the machine: missing track audio,
untranslated or empty lines, broken timing, lines the QC pass flagged and
output names that cannot be written portably. Pure function over the job
dict (artifact existence is injected) so the rules are unit-testable.
"""

from __future__ import annotations

import os
from typing import Callable

from core.path_security import portable_filename

ERROR = "error"
WARNING = "warning"
INFO = "info"


def _issue(code: str, severity: str, **extra) -> dict:
    return {"code": code, "severity": severity, **{k: v for k, v in extra.items() if v is not None}}


def run_preflight(
    job: dict,
    segments_for_lang: Callable[[dict, str], list],
    artifact_exists: Callable[[object], bool],
) -> dict:
    issues: list[dict] = []
    segments = job.get("segments") or []
    tracks = job.get("dubbed_tracks") or {}

    base = os.path.splitext(str(job.get("filename") or ""))[0]
    if not base or portable_filename(base, "") != base:
        issues.append(_issue("unsafe_filename", WARNING, value=base))

    if not segments:
        issues.append(_issue("no_segments", ERROR))
    for index, seg in enumerate(segments):
        start, end = seg.get("start"), seg.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            issues.append(_issue("invalid_timing", ERROR, segment=index))
        elif index and isinstance(segments[index - 1].get("end"), (int, float)) and start < segments[index - 1]["end"] - 0.05:
            issues.append(_issue("overlapping_segments", WARNING, segment=index))

    if not tracks:
        issues.append(_issue("no_tracks", ERROR))
    for lang, track in tracks.items():
        if not artifact_exists((track or {}).get("path")):
            issues.append(_issue("track_audio_missing", ERROR, lang=lang))
        for index, seg in enumerate(segments_for_lang(job, lang)):
            if not str(seg.get("text") or "").strip():
                issues.append(_issue("empty_line", WARNING, lang=lang, segment=index))

    if segments and tracks:
        if not any("qc_drift" in seg for seg in segments):
            issues.append(_issue("qc_not_run", INFO))
        for index, seg in enumerate(segments):
            if seg.get("qc_flagged"):
                issues.append(_issue("qc_flagged", WARNING, segment=index))

    counts = {level: sum(1 for i in issues if i["severity"] == level) for level in (ERROR, WARNING, INFO)}
    return {"ready": counts[ERROR] == 0, "counts": counts, "issues": issues}
