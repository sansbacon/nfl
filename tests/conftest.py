from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def duckdb_backend():
    """Fresh DuckDB in-memory backend per test."""
    import ibis

    return ibis.duckdb.connect(":memory:")
