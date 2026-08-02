"""PyIceberg persistence adapter for NFLverse datasets.

Delegates to nfl.common.storage.iceberg with NFLverse-specific
namespace routing and contract resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import polars as pl

from nfl.common.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergNamespaceConfig as _BaseNamespaceConfig,
    IcebergWriteResult,
    IcebergWriteMode as WriteMode,
    persist_to_iceberg as _persist,
)
from nfl.nflverse_fantasy.validation import get_contract


@dataclass(frozen=True, slots=True)
class IcebergNamespaceConfig(_BaseNamespaceConfig):
    """NFLverse Iceberg namespace defaults."""

    nfl: str = "nvnfl"
    common: str = "nvcommon"


def _resolve_primary_key(entity: str, sport: str | None) -> tuple[str, ...]:
    """Resolve primary key via NFLverse validation contracts."""
    contract = get_contract(entity)
    return contract.primary_key


def persist_to_iceberg(
    frames: Mapping[str, pl.DataFrame],
    namespace_config: IcebergNamespaceConfig | None = None,
    default_mode: WriteMode = "upsert",
    idempotency_store_path: str | Path = ".iceberg/nflverse_write_log.json",
    dry_run: bool = True,
) -> list[IcebergWriteResult]:
    """Write NFLverse DataFrames to Iceberg tables."""
    return _persist(
        frames,
        catalog_config=IcebergCatalogConfig(catalog_name="nflverse"),
        namespace_config=namespace_config or IcebergNamespaceConfig(),
        primary_key_resolver=_resolve_primary_key,
        default_mode=default_mode,
        idempotency_store_path=idempotency_store_path,
        sport_prefixes=("nvnfl_",),
        dry_run=dry_run,
    )
