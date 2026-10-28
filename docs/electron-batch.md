# Electron batch dubbing

Open Batch dubbing from the cloning sidebar or command search. Add video or audio
files (MP3, WAV, M4A, FLAC and other audio containers dub into an AAC `.m4a`),
choose one or more target languages, optionally select a saved voice, choose
whether to preserve background audio and pick a voice quality tier (Fast,
Balanced, High, Maximum; the default follows Settings → Performance and applies
to the VoiceStudio engine). Add to Queue submits through the existing
backend. Successfully submitted files leave the upload list; failed files remain.
The backend enforces ASR readiness and owns translation, generation and mixing.
The Electron setup sidebar accepts file picking or drag-and-drop, groups media,
languages and voice/audio choices into stable cards, and exposes the same Add Videos
action from the empty job view.

Active, Completed and Failed views poll backend jobs. Progress shows backend stages
and percentages. Active jobs can be cancelled; finished records require an inline
confirmation before deletion. Completed language outputs use the native save dialog.
Every finished job also offers SRT subtitles per dubbed language, the source
transcript, and one zip with every output and subtitle file (`GET /batch/package/{id}`).
Reloading the renderer reads existing jobs and never re-enqueues them. Job records
are saved to `batch/jobs.json` in the data folder: after a backend restart finished
jobs stay downloadable, and jobs that were queued or running come back cancelled
and retryable from their saved upload. GPU work itself is never resumed mid-job. Native watch folders detect settled files through a capability-scoped
directory handle and stream multipart uploads directly to the selected local or
HTTPS remote backend. Remote uploads receive the scoped session from Electron main;
the renderer never handles it.

Verification: node electron/tests/batch-smoke.mjs uses mocked jobs to check file
selection, enqueue, progress, renderer reload, cancellation, export availability
and confirmed deletion. The enqueue unit regression covers partial failure and
language/voice/quality fields; `tests/test_batch_v2.py` covers audio inputs,
subtitles, quality tiers, the zip package, path confinement and restart recovery. The native helper smoke verifies confined streaming,
authorization replacement, rename detection and revocation. No test yet establishes
real model-backed batch completion or a separate remote-machine transfer.
