import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402


@pytest.fixture
def make_app(tmp_path):
    """Factory that builds an app with an isolated temporary log file."""
    def _make(simulation=True, **overrides):
        log_file = str(tmp_path / "compromised_access.jsonl")
        overrides.setdefault("LOG_FILE", log_file)
        overrides.setdefault("TESTING", True)
        overrides.setdefault("LAB_SIMULATION_ENABLED", simulation)
        app = create_app(**overrides)
        app._test_log_file = log_file
        return app
    return _make


@pytest.fixture
def app_and_log(make_app):
    app = make_app(simulation=True)
    return app, app._test_log_file


@pytest.fixture
def client(app_and_log):
    app, _ = app_and_log
    return app.test_client()


@pytest.fixture
def read_records():
    def _read(log_file):
        if not os.path.exists(log_file):
            return []
        records = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    return _read
