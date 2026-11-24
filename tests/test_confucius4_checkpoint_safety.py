"""Confucius4 downloads reviewed commits only, and its pickles cannot run code.

Upstream asks the Hub for the moving default branch and reads its S2A
checkpoint with ``torch.load(weights_only=False)``. The sidecar pins every
repository it downloads and forces weights-only loading while it constructs.
"""
import io
import os
import pickle
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
import torch
from engines.confucius4 import main as sc


def test_every_downloaded_repository_has_a_full_commit_pin():
    assert set(sc.REVIEWED_REVISIONS) == {
        "netease-youdao/Confucius4-TTS", "facebook/w2v-bert-2.0",
        "funasr/campplus", "nvidia/bigvgan_v2_22khz_80band_256x",
    }
    for revision in sc.REVIEWED_REVISIONS.values():
        assert len(revision) == 40 and int(revision, 16) >= 0


def _fake_hub(monkeypatch):
    calls = []

    def recorder(name):
        return lambda *args, **kwargs: calls.append((name, args, kwargs))

    hub = ModuleType("huggingface_hub")
    file_download = ModuleType("huggingface_hub.file_download")
    snapshot = ModuleType("huggingface_hub._snapshot_download")
    hub.hf_hub_download = file_download.hf_hub_download = recorder("hf_hub_download")
    hub.snapshot_download = snapshot.snapshot_download = recorder("snapshot_download")
    hub.file_download, hub._snapshot_download = file_download, snapshot
    monkeypatch.setitem(sys.modules, "huggingface_hub", hub)
    monkeypatch.setitem(sys.modules, "huggingface_hub.file_download", file_download)
    monkeypatch.setitem(sys.modules, "huggingface_hub._snapshot_download", snapshot)
    return hub, calls


def test_hub_downloads_of_reviewed_repos_get_their_pin(monkeypatch):
    hub, calls = _fake_hub(monkeypatch)
    sc._pin_hub_downloads(hub)
    sc._pin_hub_downloads(hub)  # idempotent: one wrapper, not two
    hub.hf_hub_download("netease-youdao/Confucius4-TTS", filename="s2a_model.pt")
    hub.hf_hub_download(repo_id="funasr/campplus", filename="x.bin", revision="main")
    hub.snapshot_download("facebook/w2v-bert-2.0")
    hub.hf_hub_download("someone/else", filename="f")
    hub.hf_hub_download("funasr/campplus", filename="x.bin", revision="a" * 40)
    revisions = [kwargs.get("revision") for _, _, kwargs in calls]
    assert revisions == [
        sc.REVIEWED_REVISIONS["netease-youdao/Confucius4-TTS"],
        sc.REVIEWED_REVISIONS["funasr/campplus"],
        sc.REVIEWED_REVISIONS["facebook/w2v-bert-2.0"],
        None,
        "a" * 40,
    ]
    # Libraries bind these names from the submodules too.
    sys.modules["huggingface_hub.file_download"].hf_hub_download("nvidia/bigvgan_v2_22khz_80band_256x")
    assert calls[-1][2]["revision"] == sc.REVIEWED_REVISIONS["nvidia/bigvgan_v2_22khz_80band_256x"]


class _Payload:
    def __reduce__(self):
        return (os.getcwd, ())


def test_construction_refuses_pickled_code_but_loads_state_dicts(tmp_path, monkeypatch):
    state = tmp_path / "s2a_model.pt"
    torch.save({"layer.weight": torch.zeros(2, 2)}, state)
    evil = tmp_path / "evil.pt"
    torch.save({"x": _Payload()}, evil)
    seen = {}

    def constructor(**_kwargs):
        # Upstream: torch.load(s2a_model_path, map_location="cpu", weights_only=False)
        seen["state"] = torch.load(state, map_location="cpu", weights_only=False)
        with pytest.raises(pickle.UnpicklingError):
            torch.load(evil, map_location="cpu", weights_only=False)
        return object()

    monkeypatch.setitem(sys.modules, "confuciustts.cli.inference", SimpleNamespace(ConfuciusTTS=constructor))
    monkeypatch.setattr(sc, "_model", None)
    monkeypatch.setattr(sc, "_config_path", lambda: "fixture.yaml")
    monkeypatch.setattr(sc, "_ensure_clone_on_sys_path", lambda: None)
    monkeypatch.setattr(sc, "_chdir_to_clone_if_available", lambda: None)
    pinned = Mock()
    monkeypatch.setattr(sc, "_pin_hub_downloads", pinned)
    sc._load_model(io.BytesIO())
    assert seen["state"]["layer.weight"].shape == (2, 2)
    pinned.assert_called_once()
    assert torch.load.__module__ == "torch.serialization"


def test_registry_records_the_same_pins():
    import json
    from pathlib import Path

    registry = json.loads(
        (Path(__file__).resolve().parents[1] / "backend/config/model_licenses.json").read_text(encoding="utf-8")
    )
    recorded = {m["id"]: m["runtime_revision"] for m in registry["models"] if m["id"] in sc.REVIEWED_REVISIONS}
    assert recorded == sc.REVIEWED_REVISIONS
