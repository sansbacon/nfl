"""PyIceberg persistence adapter for FantasyPros datasets.

Delegates to nfl.common.storage.iceberg with FantasyPros-specific
namespace routing and contract resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

import polars as pl

from nfl.common.storage.iceberg import (
    IcebergCatalogConfig as _BaseCatalogConfig,
    IcebergNamespaceConfig as _BaseNamespaceConfig,
    IcebergWriteResult,
    IcebergWriteMode as WriteMode,
    persist_to_iceberg as _persist,
)
from nfl.fantasypros_fantasy.validation import get_contract


@dataclass(frozen=True, slots=True)
class IcebergCatalogConfig(_BaseCatalogConfig):
    """FantasyPros Iceberg catalog defaults."""

    catalog_name: str = "fantasypros"


@dataclass(frozen=True, slots=True)
class IcebergNamespaceConfig(_BaseNamespaceConfig):
    """FantasyPros Iceberg namespace defaults."""

    nfl: str = "fpnfl"
    common: str = "fpcommon"


def _resolve_primary_key(entity: str, sport: str | None) -> tuple[str, ...]:
    """Resolve primary key via FantasyPros validation contracts."""
    contract = get_contract(entity=entity, sport=sport)
    return contract.primary_key


def persist_to_iceberg(
    frames: Mapping[str, pl.DataFrame],
    catalog_config: IcebergCatalogConfig | None = None,
    namespace_config: IcebergNamespaceConfig | None = None,
    default_mode: WriteMode = "upsert",
    idempotency_store_path: str | Path = ".iceberg/fantasypros_write_log.json",
    dry_run: bool = False,
) -> list[IcebergWriteResult]:
    """Write FantasyPros DataFrames to Iceberg tables."""
    return _persist(
        frames,
        catalog_config=catalog_config or IcebergCatalogConfig(),
        namespace_config=namespace_config or IcebergNamespaceConfig(),
        primary_key_resolver=_resolve_primary_key,
        default_mode=default_mode,
        idempotency_store_path=idempotency_store_path,
        sport_prefixes=("nfl_",),
        dry_run=dry_run,
    )
