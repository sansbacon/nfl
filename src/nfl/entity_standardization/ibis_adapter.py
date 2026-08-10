"""Ibis I/O boundary adapters for entity standardization.

The entity standardization engine is inherently row-level Python
(fuzzy matching, confidence scoring) and stays in pure Python per
ADR-002. These thin adapters convert at the boundaries:

- **Input**: ibis.Table → list[dict] (materialize before standardization)
- **Output**: StandardizationResult.tables (pl.DataFrame) → dict[str, ibis.Table]

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from typing import Any

import ibis

from nfl.entity_standardization.pipeline import (
    EntityStandardizer,
    StandardizationConfig,
    StandardizationResult,
)


def result_tables_to_ibis(
    result: StandardizationResult,
) -> dict[str, ibis.Table]:
    """Convert StandardizationResult's Polars frames to Ibis tables.

    This is the OUTPUT boundary: takes the `result.tables` dict of
    Polars DataFrames and converts each to an Ibis in-memory table
    via Arrow for downstream pipeline integration.

    Parameters
    ----------
    result : StandardizationResult
        Output from ``EntityStandardizer.standardize_batch()``.

    Returns
    -------
    dict[str, ibis.Table]
        Same table names, now as Ibis table expressions.
    """
    return {
        name: ibis.memtable(frame.to_arrow())
        for name, frame in result.tables.items()
    }


def standardize_from_ibis(
    table: ibis.Table,
    standardizer: EntityStandardizer | None = None,
    config: StandardizationConfig | None = None,
) -> StandardizationResult:
    """Run entity standardization on an Ibis table of records.

    This is the INPUT boundary: materializes the Ibis table to Python
    dicts, then delegates to the standard ``standardize_batch()`` flow.

    The input table must have the columns expected by
    ``EntityStandardizer.standardize_record()``:
    - source_system
    - source_entity_id
    - raw_player_name
    - raw_team_name
    - raw_position

    Parameters
    ----------
    table : ibis.Table
        Input records as an Ibis table expression.
    standardizer : EntityStandardizer | None
        Pre-configured standardizer instance. If None, creates a
        default one using the provided config.
    config : StandardizationConfig | None
        Configuration (only used if standardizer is None).

    Returns
    -------
    StandardizationResult
        Full standardization result with tables as Polars DataFrames.
        Use ``result_tables_to_ibis()`` to convert output to Ibis.
    """
    if standardizer is None:
        standardizer = EntityStandardizer(config=config)

    # Materialize Ibis → Python dicts at the boundary
    records: list[dict[str, Any]] = table.execute().to_dict(orient="records")

    return standardizer.standardize_batch(records)


def standardize_from_ibis_to_ibis(
    table: ibis.Table,
    standardizer: EntityStandardizer | None = None,
    config: StandardizationConfig | None = None,
) -> dict[str, ibis.Table]:
    """Full round-trip: Ibis input → standardize → Ibis output.

    Convenience function combining the input and output boundary
    adapters for pipelines that stay entirely in Ibis-land.

    Parameters
    ----------
    table : ibis.Table
        Input records (see ``standardize_from_ibis`` for schema).
    standardizer : EntityStandardizer | None
        Pre-configured standardizer instance.
    config : StandardizationConfig | None
        Configuration (only used if standardizer is None).

    Returns
    -------
    dict[str, ibis.Table]
        All standardization output tables as Ibis expressions.
    """
    result = standardize_from_ibis(
        table, standardizer=standardizer, config=config
    )
    return result_tables_to_ibis(result)
