"""dots.tts loads one reviewed checkpoint commit, and its pickles cannot run code.

dots.tts reads ``latent_stats.pt`` with ``torch.load(weights_only=False)``,
which executes whatever a pickle carries, and follows the Hub's moving ``main``
branch by default. The sidecar pins the reviewed commit and restricts every
``torch.load`` during the checkpoint load to tensors and plain numpy arrays.
"""
import io
import json
import os
import pickle
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from engines.dots_tts import main

ROOT = Path(__file__).resolve().parents[1]


def test_default_checkpoint_is_pinned_to_the_reviewed_registry_commit():
    registry = json.loads((ROOT / "backend/config/model_licenses.json").read_text(encoding="utf-8"))
    record = next(m for m in registry["models"] if m["id"] == main._DEFAULT_REPO)
    assert len(main._DEFAULT_REVISION) == 40 and int(main._DEFAULT_REVISION, 16) >= 0
    assert main._DEFAULT_REVISION == record["revision"]


def _load_with(monkeypatch, on_load=None, **env):
    calls = []

    def from_pretrained(repo, **kwargs):
        calls.append((repo, kwargs))
        if on_load:
            on_load()
        return object()

    monkeypatch.setitem(
        sys.modules, "dots_tts.runtime",
        SimpleNamespace(DotsTtsRuntime=SimpleNamespace(from_pretrained=from_pretrained)),
    )
    monkeypatch.setattr(main, "_runtime", None)
    for key in ("OMNIVOICE_DOTS_TTS_MODEL", "OMNIVOICE_DOTS_TTS_REVISION"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    main._load_runtime(io.BytesIO())
    return calls


def test_loader_requests_the_pinned_commit(monkeypatch):
    [(repo, kwargs)] = _load_with(monkeypatch)
    assert repo == main._DEFAULT_REPO
    assert kwargs["revision"] == main._DEFAULT_REVISION


def test_custom_checkpoint_uses_its_own_pin_or_none(monkeypatch):
    [(_, kwargs)] = _load_with(monkeypatch, OMNIVOICE_DOTS_TTS_MODEL="/models/dots")
    assert kwargs["revision"] is None
    [(_, kwargs)] = _load_with(
        monkeypatch, OMNIVOICE_DOTS_TTS_MODEL="me/dots", OMNIVOICE_DOTS_TTS_REVISION="a" * 40,
    )
    assert kwargs["revision"] == "a" * 40


class _Payload:
    ran = False

    def __reduce__(self):
        return (os.getcwd, ())


def test_latent_stats_shaped_file_loads_and_pickled_code_is_refused(tmp_path, monkeypatch):
    stats = tmp_path / "latent_stats.pt"
    # The reviewed file's exact layout: {"mean", "var"} float32 numpy arrays.
    torch.save({"mean": np.zeros(128, np.float32), "var": np.ones(128, np.float32)}, stats)
    evil = tmp_path / "evil.pt"
    torch.save({"mean": _Payload()}, evil)
    loaded = {}

    def library_load():
        # What dots_tts.models.dots_tts.core.IOHelper does.
        loaded["stats"] = torch.load(stats, weights_only=False)
        with pytest.raises(pickle.UnpicklingError):
            torch.load(evil, weights_only=False)

    _load_with(monkeypatch, on_load=library_load)
    assert loaded["stats"]["mean"].shape == (128,)
    assert torch.load is not None and torch.load.__module__ == "torch.serialization"
