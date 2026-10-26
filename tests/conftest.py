import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database.db as db  # noqa: E402

REAL_DB_PATH = db.DB_PATH


@pytest.fixture
def flask_app(tmp_path, monkeypatch):
    # Patch DB_PATH before importing app: importing app runs init_db() and
    # seed_db() at module level and must not touch the real database.
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    import app as app_module

    assert db.DB_PATH != REAL_DB_PATH

    # The module is cached across tests, so set up this test's database explicitly.
    db.init_db()
    db.seed_db()

    app_module.app.config.update(TESTING=True)
    return app_module.app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
