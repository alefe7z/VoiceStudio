"""Batch run report: one CSV row per job, formula-safe, downloadable."""
import csv
import io


def _rows(text):
    return list(csv.reader(io.StringIO(text.lstrip("﻿"))))


def test_report_rows_are_ordered_and_complete():
    from api.routers.batch import _REPORT_COLUMNS, build_batch_report

    jobs = [
        {"filename": "b.mp4", "status": "failed", "langs": ["fr"], "attempts": 2,
         "created_at": 200.0, "started_at": 210.0, "finished_at": 215.5, "error": "boom"},
        {"filename": "a.mp4", "status": "done", "langs": ["es", "de"],
         "outputs": {"es": "/x/es.mp4", "de": "/x/de.mp4"}, "created_at": 100.0},
    ]
    rows = _rows(build_batch_report(jobs))
    assert tuple(rows[0]) == _REPORT_COLUMNS
    assert [r[0] for r in rows[1:]] == ["a.mp4", "b.mp4"]
    a, b = (dict(zip(rows[0], r)) for r in rows[1:])
    assert a["languages"] == "es de" and a["outputs"] == "de es" and a["attempts"] == "1"
    assert a["duration_s"] == "" and a["started"] == ""
    assert b["duration_s"] == "5.5" and b["error"] == "boom" and b["attempts"] == "2"


def test_report_neutralises_spreadsheet_formulas():
    from api.routers.batch import build_batch_report

    rows = _rows(build_batch_report([{"filename": "=HYPERLINK(\"x\")", "status": "failed",
                                      "error": "+cmd", "created_at": 1.0}]))
    assert rows[1][0].startswith("'=") and rows[1][-1] == "'+cmd"


def test_report_endpoint_downloads_csv(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.routers import batch

    monkeypatch.setattr(batch, "_jobs", {"j": {"filename": "clip.mp4", "status": "done",
                                               "langs": ["es"], "created_at": 1.0}})
    app = FastAPI()
    app.include_router(batch.router)
    response = TestClient(app).get("/batch/report.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "batch-report-" in response.headers["content-disposition"]
    assert response.content.startswith("﻿".encode("utf-8"))
    assert _rows(response.content.decode("utf-8"))[1][0] == "clip.mp4"
