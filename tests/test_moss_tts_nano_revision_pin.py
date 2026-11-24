"""MOSS-TTS-Nano runs remote code only from the reviewed Hub commits.

Its checkpoint and audio tokenizer load with ``trust_remote_code=True``, so the
repository's Python files execute. Following a moving branch would run
whatever was pushed last; both paths load the pinned snapshots instead.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from engines.moss_tts_nano_subprocess import main as sidecar

ROOT = Path(__file__).resolve().parents[1]
MODEL = "OpenMOSS-Team/MOSS-TTS-Nano"
TOKENIZER = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano"


def test_both_repositories_are_pinned_to_full_commits():
    assert set(sidecar.REVIEWED_REVISIONS) == {MODEL, TOKENIZER}
    for revision in sidecar.REVIEWED_REVISIONS.values():
        assert len(revision) == 40 and int(revision, 16) >= 0
    registry = json.loads((ROOT / "backend/config/model_licenses.json").read_text(encoding="utf-8"))
    record = next(m for m in registry["models"] if m["id"] == MODEL)
    assert record["runtime_revision"] == sidecar.REVIEWED_REVISIONS[MODEL]


def test_pinned_source_downloads_the_reviewed_commit_only_for_known_repos(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "huggingface_hub.snapshot_download",
        lambda repo, **kw: calls.append((repo, kw)) or str(tmp_path / repo.split("/")[1]),
    )
    assert sidecar.pinned_source(MODEL).endswith("MOSS-TTS-Nano")
    assert sidecar.pinned_source(str(tmp_path)) == str(tmp_path)
    assert sidecar.pinned_source("me/my-nano") == "me/my-nano"
    assert calls == [(MODEL, {"revision": sidecar.REVIEWED_REVISIONS[MODEL]})]


def test_in_process_backend_pins_model_and_its_audio_tokenizer(monkeypatch):
    from services import tts_backend

    loaded = []

    class Model:
        @classmethod
        def from_pretrained(cls, source, **kwargs):
            loaded.append((source, kwargs))
            model = cls()
            model.config = SimpleNamespace(audio_tokenizer_pretrained_name_or_path=TOKENIZER)
            return model

    monkeypatch.setitem(sys.modules, "moss_tts_nano", SimpleNamespace())
    monkeypatch.setattr(tts_backend, "_moss_model_class", lambda _module: Model)
    monkeypatch.setattr(sidecar, "pinned_source", lambda source: f"pinned:{source}")
    monkeypatch.delenv("OMNIVOICE_MOSS_TTS_MODEL", raising=False)
    backend = tts_backend.MossTTSNanoBackend.__new__(tts_backend.MossTTSNanoBackend)
    backend._model = None
    monkeypatch.setattr(type(backend), "is_available", classmethod(lambda cls: (True, "")))
    backend._ensure_loaded()
    assert loaded == [(f"pinned:{MODEL}", {"trust_remote_code": True})]
    assert backend._model.config.audio_tokenizer_pretrained_name_or_path == f"pinned:{TOKENIZER}"
