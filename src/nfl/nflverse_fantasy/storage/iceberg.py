"""PyIceberg persistence adapter for NFLverse datasets.

Delegates to nfl.common.storage.iceberg with NFLverse-specific
namespace routing and contract resolution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from nfl.common.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergWriteResult,
)
from nfl.common.storage.iceberg import (
    IcebergNamespaceConfig as _BaseNamespaceConfig,
)
from nfl.common.storage.iceberg import (
    IcebergWriteMode as WriteMode,
)
from nfl.common.storage.iceberg import (
    persist_to_iceberg as _persist,
)
from nfl.nflverse_fantasy.validation import get_contract


@dataclass(frozen=True, slots=True)
class IcebergNamespaceConfig(_BaseNamespaceConfig):
    """NFLverse Iceberg namespace defaults."""

    nfl: str = "nvnfl"
    common: str = "nvcommon"

    def resolve(self, sport: str | None) -> str:
        """Route nvnfl sport prefix to the nfl namespace."""
        if sport in ("nfl", "nvnfl"):
            return self.nfl
        return self.common


def resolve_table_identifier(
    frame_name: str,
    namespace_config: IcebergNamespaceConfig | None = None,
) -> tuple[str, str]:
    """Resolve frame name to (table_identifier, entity).

    Backward-compatible helper — delegates to common parse_entity_and_sport.
    """
    from nfl.common.storage.iceberg import parse_entity_and_sport

    ns_cfg = namespace_config or IcebergNamespaceConfig()
    entity, sport = parse_entity_and_sport(frame_name, ("nvnfl_",))
    ns = ns_cfg.nfl if sport else ns_cfg.common
    return f"{ns}.{entity}", entity


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
