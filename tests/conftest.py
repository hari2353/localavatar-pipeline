"""Shared harness fixtures: every test runs in an isolated cwd so the repo tree stays clean."""
import pytest


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
