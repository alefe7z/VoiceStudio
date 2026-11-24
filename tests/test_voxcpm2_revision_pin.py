"""VoxCPM2 loads the reviewed commit the Model Catalogue installs, never Hub ``main``.

``voxcpm.VoxCPM.from_pretrained`` calls ``snapshot_download(repo_id)`` with no
revision, so a bare Hub id would follow whatever ``main`` points to today.
"""
import sys
from types import SimpleNamespace

from services import hf_revisions

REPO = "openbmb/VoxCPM2"


def test_voxcpm2_is_a_curated_repo():
    assert len(hf_revisions.revision_for(REPO)) == 40


def test_pinned_snapshot_downloads_the_curated_revision(monkeypatch, tmp_path):
    calls = []

    def snapshot_download(repo, **kwargs):
        calls.append((repo, kwargs))
        return str(tmp_path)

    monkeypatch.setattr("huggingface_hub.snapshot_download", snapshot_download)
    assert hf_revisions.pinned_snapshot(REPO) == str(tmp_path)
    assert calls == [(REPO, {"revision": hf_revisions.revision_for(REPO)})]
    # A local folder or a repo the user chose passes through untouched.
    assert hf_revisions.pinned_snapshot(str(tmp_path)) == str(tmp_path)
    assert hf_revisions.pinned_snapshot("someone/custom-voxcpm") == "someone/custom-voxcpm"
    assert len(calls) == 1


def test_in_process_backend_loads_the_pinned_snapshot(monkeypatch, tmp_path):
    from services import tts_backend

    loaded = []
    monkeypatch.setitem(sys.modules, "voxcpm", SimpleNamespace(VoxCPM=SimpleNamespace(
        from_pretrained=lambda source, **_kw: loaded.append(source) or object())))
    monkeypatch.setattr(hf_revisions, "pinned_snapshot", lambda source: f"pinned:{source}")
    monkeypatch.setattr(tts_backend.VoxCPM2Backend, "is_available", classmethod(lambda cls: (True, "")))
    monkeypatch.setattr(tts_backend, "_voxcpm_upgrade_hint", lambda: None)
    monkeypatch.delenv("OMNIVOICE_VOXCPM_MODEL", raising=False)
    backend = tts_backend.VoxCPM2Backend.__new__(tts_backend.VoxCPM2Backend)
    backend._model = None
    backend._ensure_loaded()
    assert loaded == [f"pinned:{REPO}"]


def test_sidecar_receives_and_loads_the_pinned_revision(monkeypatch, tmp_path):
    from engines.voxcpm2_subprocess import VoxCPM2SubprocessBackend
    from engines.voxcpm2_subprocess import main as sidecar

    monkeypatch.delenv("OMNIVOICE_VOXCPM_MODEL", raising=False)
    env = VoxCPM2SubprocessBackend.extra_spawn_env(object.__new__(VoxCPM2SubprocessBackend))
    assert env == {"OMNIVOICE_VOXCPM_REVISION": hf_revisions.revision_for(REPO)}

    calls = []
    monkeypatch.setattr(
        "huggingface_hub.snapshot_download",
        lambda repo, **kw: calls.append((repo, kw)) or str(tmp_path),
    )
    monkeypatch.setenv("OMNIVOICE_VOXCPM_REVISION", env["OMNIVOICE_VOXCPM_REVISION"])
    assert sidecar._pinned_checkpoint(REPO) == str(tmp_path)
    assert calls == [(REPO, {"revision": env["OMNIVOICE_VOXCPM_REVISION"]})]


def test_sidecar_gets_no_pin_for_a_checkpoint_the_user_chose(monkeypatch):
    from engines.voxcpm2_subprocess import VoxCPM2SubprocessBackend

    monkeypatch.setenv("OMNIVOICE_VOXCPM_MODEL", "/models/my-voxcpm")
    assert VoxCPM2SubprocessBackend.extra_spawn_env(object.__new__(VoxCPM2SubprocessBackend)) == {}
