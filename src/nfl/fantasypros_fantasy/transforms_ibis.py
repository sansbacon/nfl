"""Ibis-based transformation interfaces for FantasyPros datasets.

Drop-in replacement for ``transforms.py`` that produces ``ibis.Table``
expressions instead of ``pl.DataFrame`` objects. The public API mirrors
the original module:

- ``transform_entity()`` → ibis.Table
- ``transform_nfl()`` → IbisTransformResult
- ``transform()`` → dict[str, ibis.Table]

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import ibis
import pyarrow as pa

from nfl.common.validation import (
    ContractValidationError,
    EntityContract,
    validate_ibis_table,
)
from nfl.fantasypros_fantasy.validation import (
    get_contract,
    validate,
    validate_primary_key_uniqueness,
)

if TYPE_CHECKING:
    pass


class TransformValidationError(ValueError):
    """Raised when transformation outputs fail quality checks."""


@dataclass(frozen=True, slots=True)
class IbisTransformResult:
    """Transform result holding Ibis table expressions."""

    tables: dict[str, ibis.Table]


# Column type sets (same as the Polars version)
_INT_COLUMNS = {
    "season",
    "rank",
    "high",
    "low",
    "bye_week",
    "yahoo_player_id",
}
_FLOAT_COLUMNS = {
    "adp",
    "adp_espn",
    "adp_sleeper",
    "adp_cbs",
    "adp_nfl",
    "adp_rtsports",
    "adp_fantrax",
    "adp_realtime",
    "stdev",
}
_BOOL_COLUMNS = {"is_current"}


def _empty_table_for_contract(
    required: tuple[str, ...], optional: tuple[str, ...]
) -> ibis.Table:
    """Create an empty Ibis table matching the contract schema."""
    schema = {col: "string" for col in list(required + optional)}
    return ibis.memtable(pa.table({col: pa.array([], type=pa.string()) for col in schema}))


def _coerce_types(table: ibis.Table) -> ibis.Table:
    """Cast columns to their expected types based on column name sets."""
    casts: dict[str, ibis.Expr] = {}
    for col in table.columns:
        if col in _INT_COLUMNS:
            casts[col] = table[col].try_cast("int64")
        elif col in _FLOAT_COLUMNS:
            casts[col] = table[col].try_cast("float64")
        elif col in _BOOL_COLUMNS:
            casts[col] = table[col].try_cast("boolean")
    return table.mutate(**casts) if casts else table


def _sorted_by_primary_key(
    table: ibis.Table, primary_key: tuple[str, ...]
) -> ibis.Table:
    """Order the table by primary key columns present in the schema."""
    keys = [k for k in primary_key if k in table.columns]
    return table.order_by(keys) if keys else table


def transform_entity(
    records: Iterable[Mapping[str, Any]],
    entity: str,
    sport: str | None = None,
    keep_extra_fields: bool = False,
) -> ibis.Table:
    """Transform raw records into a typed, validated Ibis table.

    Performs the same steps as the Polars version:
    1. Validate records against the entity contract.
    2. Convert to an Ibis table (via Arrow memtable).
    3. Coerce column types.
    4. Validate the resulting schema.
    5. Sort by primary key.

    Parameters
    ----------
    records : Iterable[Mapping[str, Any]]
        Raw records from extraction.
    entity : str
        Entity name (e.g. "fp_player", "fp_adp_snapshot").
    sport : str | None
        Sport code for sport-scoped contracts.
    keep_extra_fields : bool
        If True, retains fields not in the contract.

    Returns
    -------
    ibis.Table
        Typed and validated Ibis table expression.
    """
    contract = get_contract(entity=entity, sport=sport)  # type: ignore[arg-type]
    records_list = list(records)

    # Validate raw records (reuse existing validation logic)
    try:
        validate(records_list, entity=entity, sport=sport)  # type: ignore[arg-type]
    except Exception as exc:
        raise TransformValidationError(str(exc)) from exc

    if not records_list:
        return _coerce_types(
            _empty_table_for_contract(contract.required, contract.optional)
        )

    # Build the record set
    if keep_extra_fields:
        data = records_list
    else:
        allowed = list(contract.required + contract.optional)
        data = [{field: row.get(field) for field in allowed} for row in records_list]

    # Convert to Ibis via Arrow memtable
    table = ibis.memtable(data)

    # Coerce types
    table = _coerce_types(table)

    # Validate schema using the new common validator
    ibis_contract = EntityContract(
        name=contract.name,
        required=contract.required,
        optional=contract.optional,
        primary_key=contract.primary_key,
    )
    try:
        validate_ibis_table(table, ibis_contract, allow_extra_columns=keep_extra_fields)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    return _sorted_by_primary_key(table, contract.primary_key)


def transform_nfl(
    adp_snapshots: Iterable[Mapping[str, Any]] | None = None,
    yahoo_player_map: Iterable[Mapping[str, Any]] | None = None,
) -> IbisTransformResult:
    """Transform NFL-scoped FantasyPros entities."""
    return IbisTransformResult(
        tables={
            "fp_adp_snapshot": transform_entity(
                adp_snapshots or [], entity="fp_adp_snapshot", sport="nfl"
            ),
            "fp_yahoo_player_map": transform_entity(
                yahoo_player_map or [], entity="fp_yahoo_player_map", sport="nfl"
            ),
        }
    )


def transform(
    common_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    nfl_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, ibis.Table]:
    """Transform all FantasyPros entities into Ibis tables.

    Parameters
    ----------
    common_entities : Mapping[str, Iterable[Mapping[str, Any]]] | None
        Sport-agnostic entities (e.g. fp_player).
    nfl_entities : Mapping[str, Iterable[Mapping[str, Any]]] | None
        NFL-scoped entities (e.g. fp_adp_snapshot).

    Returns
    -------
    dict[str, ibis.Table]
        Entity name to Ibis table mapping.
    """
    common_entities = common_entities or {}
    nfl_entities = nfl_entities or {}

    common_tables = {
        "fp_player": transform_entity(
            common_entities.get("fp_player", []), entity="fp_player"
        )
    }

    nfl = transform_nfl(
        adp_snapshots=nfl_entities.get("fp_adp_snapshot", []),
        yahoo_player_map=nfl_entities.get("fp_yahoo_player_map", []),
    )

    return {
        **common_tables,
        **{f"nfl_{name}": table for name, table in nfl.tables.items()},
    }
