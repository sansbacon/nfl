"""Pipeline orchestration for Yahoo Fantasy data (DEPRECATED).

.. deprecated:: 1.0.0
    This legacy pipeline orchestrator is deprecated. Use the Ibis-based
    transforms and ``nfl.common.storage.persist_tables()`` directly:

        from nfl.common.backend import get_backend
        from nfl.common.storage import persist_tables
        from nfl.yahoo_fantasy.transforms_ibis import transform
        
        backend = get_backend(config)
        tables = transform(...)
        persist_tables(tables, backend)
"""

from __future__ import annotations

import warnings

warnings.warn(
    "nfl.yahoo_fantasy.pipeline is deprecated. "
    "Use nfl.yahoo_fantasy.transforms_ibis + nfl.common.storage.persist_tables() instead.",
    DeprecationWarning,
    stacklevel=2,
)
