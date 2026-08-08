"""PyIceberg persistence adapter for FantasyPros datasets.

Delegates to nfl.common.storage.iceberg with FantasyPros-specific
namespace routing and contract resolution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from nfl.common.storage.iceberg import (
    IcebergCatalogConfig as _BaseCatalogConfig,
)
from nfl.common.storage.iceberg import (
    IcebergNamespaceConfig as _BaseNamespaceConfig,
)
from nfl.common.storage.iceberg import (
    IcebergWriteMode as WriteMode,
)
from nfl.common.storage.iceberg import (
    IcebergWriteResult,
)
from nfl.common.storage.iceberg import (
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


def resolve_table_identifier(
    frame_name: str,
    namespace_config: IcebergNamespaceConfig,
) -> tuple[str, str, str | None]:
    """Resolve frame name to (table_identifier, entity, sport).

    Backward-compatible helper — delegates to common parse_entity_and_sport.
    """
    from nfl.common.storage.iceberg import parse_entity_and_sport

    entity, sport = parse_entity_and_sport(frame_name, ("nfl_", "nba_"))
    if sport == "nfl":
        ns = namespace_config.nfl
    elif sport == "nba" and hasattr(namespace_config, "nba"):
        ns = namespace_config.nba
    else:
        ns = namespace_config.common
    return f"{ns}.{entity}", entity, sport


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
