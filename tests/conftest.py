"""Pytest configuration for local temporary directories."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


def pytest_configure() -> None:
    root = Path(__file__).resolve().parents[1]
    tmp_root = root / ".pytest_tmp"
    tmp_root.mkdir(exist_ok=True)
    tempfile.tempdir = str(tmp_root)
    os.environ["TMP"] = str(tmp_root)
    os.environ["TEMP"] = str(tmp_root)
    os.environ["TMPDIR"] = str(tmp_root)


@pytest.fixture
def tmp_path() -> Path:
    root = Path(__file__).resolve().parents[1] / ".pytest_tmp"
    root.mkdir(exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="pytest-", dir=str(root)))
