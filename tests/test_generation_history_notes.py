"""Revision notes on takes: migration 0014, schema self-heal and the notes API."""
import os
import sqlite3

os.environ.setdefault("OMNIVOICE_MODEL", "test")
os.environ.setdefault("OMNIVOICE_DISABLE_FILE_LOG", "1")

import core.db as _db
from core.db import _BASE_SCHEMA, ensure_schema

from test_generation_takes import (  # noqa: F401  (pytest fixture)
    _cols,
    _connect,
    _insert_take,
    _run_alembic,
    _seed_pre_takes_db,
    _stamp,
    api,
)


def test_migration_0014_adds_notes_and_downgrades(tmp_path):
    dbf = tmp_path / "user.db"
    _seed_pre_takes_db(dbf)
    _stamp(str(dbf), "0008_pronunciation_dictionary")
    _run_alembic("upgrade", str(dbf))
    assert "notes" in _cols(dbf)
    _run_alembic("downgrade", str(dbf), target="0013_generation_history_design_recipe")
    assert "notes" not in _cols(dbf)


def test_migration_0014_is_noop_on_fresh_install(tmp_path):
    dbf = tmp_path / "fresh.db"
    with sqlite3.connect(str(dbf)) as conn:
        conn.executescript(_BASE_SCHEMA)
    _stamp(str(dbf), "0013_generation_history_design_recipe")
    _run_alembic("upgrade", str(dbf))
    assert "notes" in _cols(dbf)


def test_db_without_alembic_self_heals_notes(tmp_path, monkeypatch):
    dbf = tmp_path / "user.db"
    _seed_pre_takes_db(dbf)
    monkeypatch.setattr(_db, "get_db", lambda: _connect(dbf))
    ensure_schema()
    assert "notes" in _cols(dbf)


def test_notes_roundtrip_trim_clear_and_list(api):
    client, dbf, outdir, _gen = api
    _insert_take(dbf, outdir, "t1", 1.0)

    r = client.put("/history/t1/notes", json={"notes": "  v2: slower pace, approved  "})
    assert r.status_code == 200
    assert r.json() == {"id": "t1", "notes": "v2: slower pace, approved"}
    listed = {row["id"]: row for row in client.get("/history").json()}
    assert listed["t1"]["notes"] == "v2: slower pace, approved"

    r = client.put("/history/t1/notes", json={"notes": "   "})
    assert r.json()["notes"] is None
    with sqlite3.connect(str(dbf)) as conn:
        assert conn.execute("SELECT notes FROM generation_history WHERE id='t1'").fetchone()[0] is None


def test_notes_unknown_take_404s_and_rejects_oversize(api):
    client, dbf, outdir, _gen = api
    assert client.put("/history/nope/notes", json={"notes": "x"}).status_code == 404
    _insert_take(dbf, outdir, "t2", 2.0)
    assert client.put("/history/t2/notes", json={"notes": "x" * 20_001}).status_code == 422
