"""Shared storage adapters for all NFL fantasy data sources.

Primary API (Ibis-based):
- ``persist_tables()`` — write Ibis table expressions to any backend
- ``persist_from_polars()`` — bridge: Polars frames → Ibis → backend
- ``compute_record_hash()`` — SCD2 record hashing via Ibis
- ``merge_scd2()`` — backend-dispatched SCD2 merge

For Unity Catalog Delta tables and Volumes, install ``nfl-databricks``.
"""

from nfl.common.storage.ibis_writer import (
    WriteResult,
    persist_from_polars,
    persist_tables,
)
from nfl.common.storage.scd2 import (
    compute_record_hash,
    merge_scd2,
)

__all__ = [
    "WriteResult",
    "persist_tables",
    "persist_from_polars",
    "compute_record_hash",
    "merge_scd2",
]
