"""Backend-agnostic schema and quality validation for Ibis tables.

Provides contract validation that works across all Ibis backends.
Replaces per-source ``validate_polars_frame`` functions with a
unified interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ibis


class ContractValidationError(ValueError):
    """Raised when a table or record violates a contract."""


@dataclass(frozen=True, slots=True)
class EntityContract:
    """Defines the expected schema for an entity.

    Attributes
    ----------
    name : str
        Entity name (e.g. "league", "team", "player").
    required : tuple[str, ...]
        Columns that must be present.
    optional : tuple[str, ...]
        Columns that may be present but are not required.
    primary_key : tuple[str, ...]
        Columns forming the business key (for deduplication checks).
    """

    name: str
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    primary_key: tuple[str, ...] = ()

    @property
    def allowed_fields(self) -> set[str]:
        """All columns permitted by this contract."""
        return set(self.required + self.optional)


def validate_ibis_table(
    table: ibis.Table,
    contract: EntityContract,
    *,
    allow_extra_columns: bool = True,
) -> None:
    """Validate an Ibis table expression against an EntityContract.

    Checks that all required columns are present. Optionally checks
    that no unexpected columns exist.

    Parameters
    ----------
    table : ibis.Table
        Ibis table expression to validate.
    contract : EntityContract
        Expected schema contract.
    allow_extra_columns : bool
        If False, raises on columns not in ``contract.allowed_fields``.

    Raises
    ------
    ContractValidationError
        If required columns are missing or unexpected columns are found.

    Examples
    --------
    >>> import ibis
    >>> from nfl.common.validation import EntityContract, validate_ibis_table
    >>> contract = EntityContract(name="team", required=("team_key", "team_name"))
    >>> t = ibis.memtable({"team_key": ["1"], "team_name": ["Chiefs"]})
    >>> validate_ibis_table(t, contract)  # passes silently
    """
    actual_cols = set(table.columns)
    missing = set(contract.required) - actual_cols
    if missing:
        raise ContractValidationError(
            f"Missing required columns for '{contract.name}': {sorted(missing)}"
        )
    if not allow_extra_columns:
        extra = actual_cols - contract.allowed_fields
        if extra:
            raise ContractValidationError(
                f"Unexpected columns for '{contract.name}': {sorted(extra)}"
            )


def validate_not_empty(
    table: ibis.Table,
    entity: str,
) -> None:
    """Validate that a table expression is not empty.

    Parameters
    ----------
    table : ibis.Table
        Ibis table expression to check.
    entity : str
        Entity name for error messages.

    Raises
    ------
    ContractValidationError
        If the table has zero rows.
    """
    row_count = int(table.count().execute())
    if row_count == 0:
        raise ContractValidationError(
            f"Table for '{entity}' is empty (0 rows)."
        )


def validate_primary_key(
    table: ibis.Table,
    contract: EntityContract,
) -> None:
    """Validate that the primary key has no duplicates.

    Parameters
    ----------
    table : ibis.Table
        Ibis table expression to check.
    contract : EntityContract
        Contract defining the primary key.

    Raises
    ------
    ContractValidationError
        If duplicate primary key values are found.
    """
    if not contract.primary_key:
        return  # No primary key defined — skip

    pk_cols = [col for col in contract.primary_key if col in table.columns]
    if not pk_cols:
        return  # Primary key columns not present — skip

    total = int(table.count().execute())
    distinct = int(table.select(pk_cols).distinct().count().execute())

    if distinct < total:
        duplicates = total - distinct
        raise ContractValidationError(
            f"Primary key violation for '{contract.name}': "
            f"{duplicates} duplicate rows on key {pk_cols}."
        )
