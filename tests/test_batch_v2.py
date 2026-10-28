"""Batch v2: audio inputs, subtitles, per-job quality, zip package, restart survival."""
from __future__ import annotations

import asyncio
import io
import json
import os
import zipfile

os.environ.setdefault("OMNIVOICE_DISABLE_FILE_LOG", "1")

import pytest

from test_dub_batch_engine_selection import (  # noqa: F401  (pytest fixtures)
    batch_job_env,
    fake_registry,
    no_omnivoice_model_manager,
)


# ── subtitle builders ───────────────────────────────────────────────────────


def test_srt_and_vtt_skip_empty_or_untimed_cues_and_escape_vtt():
    from services.batch_subtitles import build_srt, build_vtt

    segments = [
        {"start": 0.0, "end": 1.25, "text": " Hello\n\n world "},
        {"start": 1.5, "end": 1.5, "text": "zero length"},
        {"start": 2.0, "end": 3.0, "text": "   "},
        {"start": 3.0, "end": 4.5, "text": "a < b & c --> d"},
    ]
    assert build_srt(segments) == (
        "1\n00:00:00,000 --> 00:00:01,250\nHello\nworld\n\n"
        "2\n00:00:03,000 --> 00:00:04,500\na < b & c --> d\n"
    )
    vtt = build_vtt(segments)
    assert vtt.startswith("WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.250\nHello\nworld\n")
    assert "a &lt; b &amp; c --&gt; d" in vtt


# ── pipeline ────────────────────────────────────────────────────────────────


@pytest.fixture
def recorded_commands(monkeypatch):
    commands = []

    def _run(cmd, *a, **kw):
        commands.append(list(cmd))

        class _Result:
            stdout = b""
            stderr = b"Duration: 00:00:02.00, start: 0.000000, bitrate: 1000 kb/s\n"

        return _Result()

    monkeypatch.setattr("subprocess.run", _run)
    return commands


def test_audio_input_gets_m4a_output_and_subtitles(
    batch_job_env, fake_registry, no_omnivoice_model_manager, recorded_commands, monkeypatch, tmp_path,
):
    b, make_job = batch_job_env
    fake_registry("fake-batch-audio", supports_cloning=False)
    monkeypatch.setenv("OMNIVOICE_TTS_BACKEND", "fake-batch-audio")
    job = make_job("jobaudio")
    job.update(filename="episode.mp3", video_path=str(tmp_path / "episode.mp3"))

    asyncio.run(b._run_batch_pipeline("jobaudio", job))

    output = job["outputs"]["en"]
    assert output.endswith(os.path.join("jobaudio", "output_en.m4a"))
    mix = next(cmd for cmd in recorded_commands if output in cmd)
    assert "-vn" in mix and "0:v" not in mix and "[out]" in mix
    assert set(job["subtitles"]["en"]) == {"srt", "vtt"}
    with open(job["subtitles"]["en"]["srt"], encoding="utf-8") as fh:
        assert "hola" in fh.read()
    assert job["transcript"]["lang"] == "en"
    assert os.path.isfile(job["transcript"]["vtt"])


def test_video_input_keeps_mp4_output(
    batch_job_env, fake_registry, no_omnivoice_model_manager, recorded_commands, monkeypatch,
):
    b, make_job = batch_job_env
    fake_registry("fake-batch-video", supports_cloning=False)
    monkeypatch.setenv("OMNIVOICE_TTS_BACKEND", "fake-batch-video")
    job = make_job("jobvideo")
    asyncio.run(b._run_batch_pipeline("jobvideo", job))
    output = job["outputs"]["en"]
    assert output.endswith("output_en.mp4")
    mix = next(cmd for cmd in recorded_commands if output in cmd)
    assert "0:v" in mix


@pytest.mark.parametrize(("tier", "steps", "postprocess"), [("fast", 8, False), ("max", 64, True)])
def test_job_quality_tier_sets_sampling(
    batch_job_env, fake_registry, no_omnivoice_model_manager, recorded_commands, monkeypatch,
    tier, steps, postprocess,
):
    import services.performance_profiles as perf

    b, make_job = batch_job_env
    fake = fake_registry("fake-batch-tier", supports_cloning=False)
    fake.calls = []
    monkeypatch.setenv("OMNIVOICE_TTS_BACKEND", "fake-batch-tier")
    monkeypatch.setattr(perf, "TIERED_TTS_ENGINES", frozenset({"fake-batch-tier"}))
    job = make_job("jobtier")
    job["quality"] = tier
    asyncio.run(b._run_batch_pipeline("jobtier", job))
    _text, kwargs = fake.calls[0]
    assert kwargs["num_step"] == steps
    assert kwargs["postprocess_output"] is postprocess


def test_tts_defaults_ignores_unknown_tier(monkeypatch):
    import services.performance_profiles as perf

    monkeypatch.setattr(perf, "requested_tier", lambda family: None)
    assert perf.tts_defaults("omnivoice", "bogus") == {}
    assert perf.tts_defaults("omnivoice", "quality") == {"num_step": 32, "postprocess_output": True}
    assert perf.tts_defaults("kittentts", "quality") == {}


# ── endpoints ───────────────────────────────────────────────────────────────


@pytest.fixture
def batch_api(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.routers import batch

    monkeypatch.setattr(batch, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(batch, "_jobs", {})
    monkeypatch.setattr(batch, "_restored", True)
    app = FastAPI()
    app.include_router(batch.router)
    return batch, TestClient(app), tmp_path


def _done_job(batch, root, job_id="done1"):
    folder = root / "batch" / job_id
    folder.mkdir(parents=True)
    files = {}
    for name, body in {
        "output_es.m4a": b"m4a-bytes",
        "subtitles_es.srt": "1\n00:00:00,000 --> 00:00:01,000\nhola\n",
        "subtitles_es.vtt": "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nhola\n",
        "transcript_en.srt": "1\n00:00:00,000 --> 00:00:01,000\nhello\n",
        "transcript_en.vtt": "WEBVTT\n",
    }.items():
        path = folder / name
        path.write_bytes(body if isinstance(body, bytes) else body.encode())
        files[name] = str(path)
    batch._jobs[job_id] = {
        "id": job_id, "status": "done", "filename": "Ep: 1.mp3", "langs": ["es"],
        "created_at": 1.0, "input_kind": "audio",
        "outputs": {"es": files["output_es.m4a"]},
        "subtitles": {"es": {"srt": files["subtitles_es.srt"], "vtt": files["subtitles_es.vtt"]}},
        "transcript": {"lang": "en", "srt": files["transcript_en.srt"], "vtt": files["transcript_en.vtt"]},
    }
    return job_id


def test_enqueue_rejects_unknown_quality(batch_api):
    _batch, client, _root = batch_api
    response = client.post(
        "/batch/enqueue",
        files={"video": ("a.mp3", b"x", "audio/mpeg")},
        data={"langs": "es", "quality": "ultra"},
    )
    assert response.status_code == 422


def test_download_serves_audio_output_with_its_extension(batch_api):
    batch, client, root = batch_api
    job_id = _done_job(batch, root)
    response = client.get(f"/batch/download/{job_id}/es")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mp4"
    assert "Ep_%201_es.m4a" in response.headers["content-disposition"]
    assert response.content == b"m4a-bytes"


def test_subtitles_endpoint_serves_language_and_original(batch_api):
    batch, client, root = batch_api
    job_id = _done_job(batch, root)
    srt = client.get(f"/batch/subtitles/{job_id}/es")
    assert srt.status_code == 200 and "hola" in srt.text
    vtt = client.get(f"/batch/subtitles/{job_id}/original", params={"format": "vtt"})
    assert vtt.status_code == 200 and vtt.headers["content-type"].startswith("text/vtt")
    assert "en_original.vtt" in vtt.headers["content-disposition"]
    assert client.get(f"/batch/subtitles/{job_id}/fr").status_code == 404
    assert client.get(f"/batch/subtitles/{job_id}/es", params={"format": "ass"}).status_code == 422


def test_package_zips_every_output_and_cleans_up(batch_api):
    batch, client, root = batch_api
    job_id = _done_job(batch, root)
    response = client.get(f"/batch/package/{job_id}")
    assert response.status_code == 200
    names = set(zipfile.ZipFile(io.BytesIO(response.content)).namelist())
    assert names == {
        "Ep_ 1_es.m4a",
        "subtitles/Ep_ 1_es.srt", "subtitles/Ep_ 1_es.vtt",
        "subtitles/Ep_ 1_en_original.srt", "subtitles/Ep_ 1_en_original.vtt",
    }
    assert not [n for n in os.listdir(root / "batch" / job_id) if n.startswith("package-")]


def test_files_outside_the_job_folder_are_never_served(batch_api, tmp_path):
    batch, client, root = batch_api
    job_id = _done_job(batch, root)
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    batch._jobs[job_id]["outputs"]["es"] = str(outside)
    batch._jobs[job_id]["subtitles"] = {"es": {"srt": str(outside)}}
    batch._jobs[job_id]["transcript"] = {}
    assert client.get(f"/batch/download/{job_id}/es").status_code == 404
    assert client.get(f"/batch/subtitles/{job_id}/es").status_code == 404
    assert client.get(f"/batch/package/{job_id}").status_code == 404


# ── restart survival ────────────────────────────────────────────────────────


def test_jobs_survive_a_restart(batch_api, tmp_path):
    batch, client, root = batch_api
    job_id = _done_job(batch, root)
    upload = root / "batch" / "run1.mp4"
    upload.write_bytes(b"video")
    batch._jobs["run1"] = {
        "id": "run1", "status": "running", "filename": "b.mp4", "langs": ["fr"],
        "video_path": str(upload), "created_at": 2.0, "progress": {"stage": "generate"},
        "segments": [{"text": "not persisted"}],
    }
    batch._jobs["evil1"] = {
        "id": "evil1", "status": "failed", "filename": "c.mp4", "langs": ["fr"],
        "video_path": str(tmp_path / "elsewhere.mp4"), "created_at": 3.0,
    }
    batch._save_jobs()
    saved = json.loads((root / "batch" / "jobs.json").read_text())
    assert "segments" not in saved["jobs"][1]

    batch._jobs.clear()
    batch._restored = False
    jobs = {job["id"]: job for job in client.get("/batch/jobs").json()}

    assert jobs[job_id]["status"] == "done"
    assert client.get(f"/batch/download/{job_id}/es").status_code == 200
    interrupted = jobs["run1"]
    assert interrupted["status"] == "cancelled" and interrupted["retry_ready"] is True
    assert interrupted["progress"] is None and "closed" in interrupted["error"]
    assert interrupted["video_path"] == str(upload)
    assert jobs["evil1"]["video_path"] is None


def test_corrupt_job_list_is_ignored(batch_api):
    batch, client, root = batch_api
    (root / "batch").mkdir()
    (root / "batch" / "jobs.json").write_text(json.dumps({"jobs": [
        "nope", {"id": "../x", "status": "done", "filename": "a", "langs": []},
        {"id": "ok1", "status": "weird", "filename": "a", "langs": []},
        {"id": "ok2", "status": "done", "filename": "a"},
    ]}))
    batch._restored = False
    assert client.get("/batch/jobs").json() == []
    (root / "batch" / "jobs.json").write_text("{not json")
    batch._restored = False
    assert client.get("/batch/jobs").json() == []


def test_delete_persists_the_removal(batch_api):
    batch, client, root = batch_api
    job_id = _done_job(batch, root)
    batch._save_jobs()
    assert client.delete(f"/batch/jobs/{job_id}").status_code == 200
    saved = json.loads((root / "batch" / "jobs.json").read_text())
    assert saved["jobs"] == []
