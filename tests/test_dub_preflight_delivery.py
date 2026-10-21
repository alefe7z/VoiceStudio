"""Dub delivery preflight and the one-zip delivery package."""

import io
import json
import os
import uuid
import zipfile

import pytest

os.environ.setdefault("OMNIVOICE_MODEL", "test")


def _segments_for_lang(job, lang):
    texts = (job.get("segments_i18n") or {}).get(lang) or {}
    return [{**s, "text": texts.get(str(s.get("id")), s.get("text"))} for s in job.get("segments", [])]


def _job(**overrides):
    job = {
        "filename": "clip.mp4",
        "segments": [
            {"id": "a", "start": 0.0, "end": 1.0, "text": "hello"},
            {"id": "b", "start": 1.0, "end": 2.0, "text": "world"},
        ],
        "dubbed_tracks": {"es": {"path": "es.wav", "language": "Spanish"}},
    }
    job.update(overrides)
    return job


def _codes(report):
    return {issue["code"] for issue in report["issues"]}


def test_preflight_clean_job_is_ready_and_suggests_qc():
    from services.dub_preflight import run_preflight

    report = run_preflight(_job(), _segments_for_lang, lambda _path: True)
    assert report["ready"] is True
    assert _codes(report) == {"qc_not_run"}


def test_preflight_reports_each_problem_class():
    from services.dub_preflight import run_preflight

    job = _job(
        filename="bad:name?.mp4",
        segments=[
            {"id": "a", "start": 0.0, "end": 1.5, "text": "hi", "qc_drift": 0.9, "qc_flagged": True},
            {"id": "b", "start": 1.0, "end": 2.0, "text": "there", "qc_drift": 0.0},
            {"id": "c", "start": 3.0, "end": 3.0, "text": "x", "qc_drift": 0.0},
        ],
        segments_i18n={"es": {"b": "  "}},
    )
    report = run_preflight(job, _segments_for_lang, lambda _path: False)
    assert report["ready"] is False
    assert _codes(report) == {
        "unsafe_filename", "overlapping_segments", "invalid_timing",
        "track_audio_missing", "empty_line", "qc_flagged",
    }


def test_preflight_without_tracks_or_segments_blocks_delivery():
    from services.dub_preflight import run_preflight

    report = run_preflight(_job(segments=[], dubbed_tracks={}), _segments_for_lang, lambda _p: True)
    assert {"no_segments", "no_tracks"} <= _codes(report)
    assert report["ready"] is False


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app, client=("127.0.0.1", 50000))


@pytest.fixture()
def delivered_job():
    from core.config import DUB_DIR
    from services.dub_pipeline import _dub_jobs

    job_id = "t" + uuid.uuid4().hex[:10]
    job_dir = os.path.join(DUB_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    wav = os.path.join(job_dir, "dubbed_es.wav")
    with open(wav, "wb") as fh:
        fh.write(b"RIFF0000WAVE")
    job = _job(dubbed_tracks={"es": {"path": wav, "language": "Spanish", "duration": 2.0}})
    _dub_jobs[job_id] = job
    yield job_id, job
    _dub_jobs.pop(job_id, None)
    import shutil
    shutil.rmtree(job_dir, ignore_errors=True)


def test_preflight_endpoint(client, delivered_job):
    job_id, _ = delivered_job
    response = client.get(f"/dub/preflight/{job_id}")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_delivery_zip_contains_audio_subtitles_notes_and_manifest(client, delivered_job):
    job_id, _ = delivered_job
    response = client.get(f"/dub/delivery/{job_id}", params={"notes": "Approved by client"})
    assert response.status_code == 200, response.text
    assert "clip_delivery.zip" in response.headers["content-disposition"]
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert {
        "audio/clip_es_dialogue.wav", "subtitles/clip_es.srt", "subtitles/clip_es.vtt",
        "notes.txt", "manifest.json",
    } <= names
    assert archive.read("notes.txt").decode().strip() == "Approved by client"
    assert "hello" in archive.read("subtitles/clip_es.srt").decode()
    manifest = json.loads(archive.read("manifest.json"))
    assert manifest["tracks"][0]["language_code"] == "es"
    assert manifest["preflight"]["ready"] is True
    # The temporary zip is removed once served.
    from core.config import DUB_DIR
    exports = os.path.join(DUB_DIR, job_id, "exports")
    assert not [n for n in os.listdir(exports) if n.startswith("delivery-")]


def test_delivery_refuses_when_preflight_fails(client, delivered_job):
    job_id, job = delivered_job
    job["dubbed_tracks"]["es"]["path"] = os.path.join(os.path.dirname(job["dubbed_tracks"]["es"]["path"]), "gone.wav")
    response = client.get(f"/dub/delivery/{job_id}")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "dub_preflight_failed"
