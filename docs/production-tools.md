# Production tools

Tools for repeat production work. They are part of the app and need no licence or account.

## Delivery check (Dubbing)

The dub export panel runs a delivery check whenever the tracks change, and on **Check again**. It reports:

- **Errors** (block the delivery package): no transcript lines, no dubbed track, a track whose audio file is missing, a line that ends before it starts.
- **Warnings**: a line with no text in a track, a line that overlaps the previous one, a line the quality check flagged, a source file name with characters some systems reject.
- **Info**: the quality check has not run yet.

API: `GET /dub/preflight/{job_id}` returns `{ready, counts, issues[]}`.

## Delivery package (Dubbing)

Choose **Delivery package** in the export panel to save one zip named after the source file:

```
audio/<name>_<lang>_dialogue.wav   per dubbed track
audio/<name>_background.wav        when background separation ran
subtitles/<name>_<lang>.srt|.vtt   per dubbed track, on the track's fitted timing
notes.txt                          the project notes typed in the panel
manifest.json                      tracks, files and the delivery-check report
```

The package is refused (HTTP 409, `dub_preflight_failed`) while the delivery check reports errors. API: `GET /dub/delivery/{job_id}?notes=…`.

## Revision notes and versions (Clone / Design takes)

Open a take to add revision notes (approvals, what changed). Takes generated from the same text are listed as versions of that line: pick one to play it next to the current take, or open it to reuse it without generating again. Notes are stored with the take in the local database (`generation_history.notes`, migration 0014). API: `PUT /history/{id}/notes`.

## Batch rules, output names and job report (Batch)

- **Output file name**: a template with `{name}` (source file without extension), `{lang}`, `{date}` (YYYY-MM-DD the job was queued) and `{job}`. Characters Windows rejects become `_`. Default `{name}_{lang}`.
- **Batch rules**: save the target languages, voice, background setting and output template under a name, then apply them in one click. Rules are kept on this device.
- **Job report**: saves a CSV of every batch job in this session (file, status, languages, outputs, attempts, times, duration, error). API: `GET /batch/report.csv`.
