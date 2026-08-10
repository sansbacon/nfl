"""Ibis backend factory and connection lifecycle management.

Provides a single entry point for resolving an Ibis backend connection
from pipeline configuration. Supports DuckDB (default), Polars,
PySpark (Databricks/Unity Catalog), and DataFusion.

Requires: pip install nfl[ibis] (or nfl[ibis-polars], nfl[ibis-pyspark], etc.)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from nfl.common.config import BackendType, PipelineConfigBase

if TYPE_CHECKING:
    import ibis


def _import_ibis() -> Any:
    """Lazy-import ibis with a helpful error message."""
    try:
        import ibis
    except ImportError as exc:
        raise ImportError(
            "Ibis is required for backend operations. "
            "Install it with: pip install nfl[ibis]"
        ) from exc
    return ibis


def get_backend(
    config: PipelineConfigBase | None = None,
    *,
    backend: BackendType | None = None,
    duckdb_path: str | os.PathLike[str] | None = None,
) -> ibis.BaseBackend:
    """Resolve an Ibis backend connection from pipeline config.

    Parameters
    ----------
    config : PipelineConfigBase | None
        Pipeline configuration. If provided, ``backend`` and ``duckdb_path``
        are read from it (unless explicitly overridden).
    backend : BackendType | None
        Override for the backend type. Takes precedence over ``config.backend``.
        Falls back to the ``NFL_BACKEND`` environment variable, then ``"duckdb"``.
    duckdb_path : str | os.PathLike | None
        Override for the DuckDB database path. Takes precedence over
        ``config.duckdb_path``. Falls back to ``NFL_DUCKDB_PATH`` env var.

    Returns
    -------
    ibis.BaseBackend
        A connected Ibis backend instance.

    Raises
    ------
    ValueError
        If the resolved backend type is not supported.
    ImportError
        If the required backend package is not installed.

    Examples
    --------
    >>> from nfl.common.backend import get_backend
    >>> from nfl.common.config import PipelineConfigBase
    >>> config = PipelineConfigBase(backend="duckdb", duckdb_path=":memory:")
    >>> backend = get_backend(config)
    >>> backend.name
    'duckdb'
    """
    ibis = _import_ibis()

    # Resolve backend type: explicit arg > config > env var > default
    resolved_backend: BackendType = (
        backend
        or (config.backend if config else None)
        or os.getenv("NFL_BACKEND", "duckdb")  # type: ignore[assignment]
    )

    match resolved_backend:
        case "duckdb":
            resolved_path = str(
                duckdb_path
                or (config.duckdb_path if config else None)
                or os.getenv("NFL_DUCKDB_PATH", "./output/nfl.duckdb")
            )
            return ibis.duckdb.connect(resolved_path)

        case "polars":
            try:
                return ibis.polars.connect()
            except AttributeError as exc:
                raise ImportError(
                    "Ibis Polars backend requires: pip install nfl[ibis-polars]"
                ) from exc

        case "pyspark":
            try:
                # In Databricks, SparkSession is already active.
                # ibis.pyspark.connect() auto-discovers it.
                return ibis.pyspark.connect()
            except Exception as exc:
                raise ImportError(
                    "Ibis PySpark backend requires an active SparkSession and: "
                    "pip install nfl[ibis-pyspark]"
                ) from exc

        case "datafusion":
            try:
                return ibis.datafusion.connect()
            except AttributeError as exc:
                raise ImportError(
                    "Ibis DataFusion backend requires: "
                    "pip install ibis-framework[datafusion]"
                ) from exc

        case _:
            raise ValueError(
                f"Unsupported backend: {resolved_backend!r}. "
                f"Choose from: 'duckdb', 'polars', 'pyspark', 'datafusion'."
            )


def get_backend_from_env() -> ibis.BaseBackend:
    """Convenience: resolve backend entirely from environment variables.

    Reads NFL_BACKEND and NFL_DUCKDB_PATH from the environment.
    Useful for CI, Docker, and scripts.

    Returns
    -------
    ibis.BaseBackend
    """
    return get_backend()
