"""SubRip and WebVTT subtitles for batch dub tracks.

Batch segments are fresh ASR output or its translation, so cue text is plain:
SubRip writes it as-is, WebVTT escapes `<`, `&` and `-->`. Blank lines would end
a cue early, so a cue's lines are stripped and empty ones dropped.
"""
from __future__ import annotations

from services.srt_parser import escape_webvtt_text, format_cue_timestamp


def _cues(segments: list[dict]):
    index = 0
    for seg in segments:
        lines = [line.strip() for line in str(seg.get("text") or "").splitlines()]
        text = "\n".join(line for line in lines if line)
        start, end = seg.get("start"), seg.get("end")
        if not text or not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            continue
        index += 1
        yield index, float(start), float(end), text


def build_srt(segments: list[dict]) -> str:
    blocks = [
        f"{i}\n{format_cue_timestamp(s, ',')} --> {format_cue_timestamp(e, ',')}\n{text}\n"
        for i, s, e, text in _cues(segments)
    ]
    return "\n".join(blocks)


def build_vtt(segments: list[dict]) -> str:
    blocks = [
        f"{i}\n{format_cue_timestamp(s, '.')} --> {format_cue_timestamp(e, '.')}\n"
        f"{escape_webvtt_text(text, preserve_markup=False)}\n"
        for i, s, e, text in _cues(segments)
    ]
    return "WEBVTT\n\n" + "\n".join(blocks)
