# Model and download integrity

Every model VoiceStudio downloads from Hugging Face is fixed to a reviewed
commit, and model files that could run code when opened are either reviewed or
opened in a mode that cannot run code. This page records how, and what is still
outside that guarantee.

## What is pinned

- **Model Catalogue entries and their dependencies** download the commit in
  `backend/config/model_licenses.json` (`runtime_pin_scope: central`);
  `tests/test_hf_revisions.py` fails on an unpinned catalogue repository.
- **Optional engines** install their source from a reviewed GitHub commit
  (`source_revision` in `backend/services/sidecar_install.py`).
- **Engines that download their own weights on first use** load reviewed
  commits instead of the Hub's moving `main` branch:

| Engine | Repositories | Where the pin lives |
|---|---|---|
| dots.tts | `rednote-hilab/dots.tts-soar` | `backend/engines/dots_tts/main.py` |
| VoxCPM2 | `openbmb/VoxCPM2` (the catalogue commit) | `backend/config/model_licenses.json` |
| MOSS-TTS-Nano | `OpenMOSS-Team/MOSS-TTS-Nano`, `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano` | `backend/engines/moss_tts_nano_subprocess/main.py` |
| Confucius4-TTS | `netease-youdao/Confucius4-TTS`, `facebook/w2v-bert-2.0`, `funasr/campplus`, `nvidia/bigvgan_v2_22khz_80band_256x` | `backend/engines/confucius4/main.py` |

A pinned commit always serves the same files, so a change pushed to the
repository later, or a compromised account, cannot change what is installed.
Setting your own checkpoint (`OMNIVOICE_*_MODEL`) loads what you chose instead.

## Files that could run code

- **Pickle checkpoints** (`.pt`, `.pth`, `.bin`, `.ckpt`). dots.tts and
  Confucius4 open theirs with `torch.load(weights_only=False)`, which runs any
  code a pickle carries. VoiceStudio forces weights-only loading while those
  engines load, so a file that carries anything but weights fails to load
  instead of running. The pinned files were inspected without being executed:
  dots.tts `latent_stats.pt` holds two float32 arrays, Confucius4
  `s2a_model.pt` is a plain state dict. VoxCPM2 and transformers 4.57 already
  load weights-only.
- **Remote code** (`trust_remote_code`). MOSS-TTS-Nano runs Python files from
  its two repositories. The pinned files were read in full: model code only,
  with no network, process or file access beyond the model's caches.

## Updates

Desktop updates come only from this fork's own releases; see
[Desktop updates](update-channels.md).

## Still outside the guarantee

- Speech-recognition models that some engines fetch by name without a pin:
  faster-whisper's `tiny`/`large-v2` aliases, whisper.cpp GGML files,
  OmniVoice GGUF and FunASR SenseVoice (from ModelScope). These are data
  formats except SenseVoice, whose checkpoint is a pickle.
- Community gallery voices (opt-in) are third-party audio and presets read
  from the gallery's current manifest.
- **yt-dlp → Update** installs the newest yt-dlp from PyPI, by design.
- Models you add yourself from a local folder or another repository.

Pinning proves *integrity*: you get exactly the files that were reviewed. It
does not certify that a model's own code or weights are free of defects.
