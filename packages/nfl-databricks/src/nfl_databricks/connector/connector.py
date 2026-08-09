"""nflverse Community Connector for Lakeflow Connect.

Ingests NFL data from nflverse via the nflreadpy package.
See: https://github.com/nflverse/nflreadpy

Required pip install: nflreadpy

Play-by-play incremental mode
------------------------------
play_by_play supports two modes controlled by the table-level option
``pbp_incremental`` (default: "false"):

  pbp_incremental=false  (default)
      Full snapshot on every run. Simple but slow for large season ranges.

  pbp_incremental=true
      - Initial run (empty offset): loads ALL seasons in the ``seasons``
        parameter and writes them via cdc (upsert on play_id + game_id).
        Stores {"initial_load_complete": true, "latest_season": <year>}
        as the offset.
      - Subsequent runs: reloads ONLY the latest season in ``seasons``
        and merges it in.  Historical seasons are never re-fetched.

Recommended config when using incremental mode:
  seasons      = 2000,2001,...,2024   (full history on first run)
  pbp_incremental = true
"""
from __future__ import annotations

from typing import Iterator

import nflreadpy
import polars as pl
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_seasons(options: dict[str, str]) -> list[int]:
    """Parse comma-separated seasons string into a list of ints."""
    raw = options.get("seasons", "")
    if not raw:
        raise ValueError("'seasons' option is required (e.g. '2022,2023,2024')")
    return [int(s.strip()) for s in raw.split(",")]


def _parse_season_type(options: dict[str, str]) -> str:
    return options.get("season_type", "REG").upper()


def _df_to_dicts(df: pl.DataFrame) -> list[dict]:
    """Convert a Polars DataFrame to a list of JSON-serialisable dicts."""
    return df.to_dicts()


def _infer_spark_schema(df: pl.DataFrame) -> StructType:
    """Build a StructType from Polars dtypes (best-effort)."""
    type_map: dict[type, DoubleType | IntegerType | StringType] = {
        pl.Int8: IntegerType(),
        pl.Int16: IntegerType(),
        pl.Int32: IntegerType(),
        pl.Int64: IntegerType(),
        pl.UInt8: IntegerType(),
        pl.UInt16: IntegerType(),
        pl.UInt32: IntegerType(),
        pl.UInt64: IntegerType(),
        pl.Float32: DoubleType(),
        pl.Float64: DoubleType(),
    }
    fields = []
    for name, dtype in zip(df.columns, df.dtypes):
        spark_type = type_map.get(type(dtype), StringType())
        fields.append(StructField(name, spark_type, nullable=True))
    return StructType(fields)


# ---------------------------------------------------------------------------
# Table registry
# ---------------------------------------------------------------------------

TABLE_REGISTRY: dict[str, dict] = {
    "play_by_play": {
        "load": None,
        "ingestion_type": "cdc",
        "primary_keys": ["play_id", "game_id"],
        "cursor_field": None,
    },
    "player_stats_weekly": {
        "load": lambda seasons, _st: nflreadpy.load_player_stats(
            seasons=seasons, summary_level="week"
        ),
        "ingestion_type": "snapshot",
        "primary_keys": ["player_id", "season", "week", "season_type"],
        "cursor_field": None,
    },
    "player_stats_seasonal": {
        "load": lambda seasons, st: nflreadpy.load_player_stats(
            seasons=seasons,
            summary_level="reg+post" if st == "REG_POST" else st.lower(),
        ),
        "ingestion_type": "snapshot",
        "primary_keys": ["player_id", "season", "season_type"],
        "cursor_field": None,
    },
    "schedules": {
        "load": lambda seasons, _st: nflreadpy.load_schedules(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["game_id"],
        "cursor_field": None,
    },
    "rosters": {
        "load": lambda seasons, _st: nflreadpy.load_rosters(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["player_id", "season", "week"],
        "cursor_field": None,
    },
    "teams": {
        "load": lambda _seasons, _st: nflreadpy.load_teams(),
        "ingestion_type": "snapshot",
        "primary_keys": ["team_abbr"],
        "cursor_field": None,
    },
    "snap_counts": {
        "load": lambda seasons, _st: nflreadpy.load_snap_counts(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["pfr_player_id", "season", "week"],
        "cursor_field": None,
    },
    "depth_charts": {
        "load": lambda seasons, _st: nflreadpy.load_depth_charts(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["gsis_id", "season", "week", "position", "depth_position"],
        "cursor_field": None,
    },
    "injuries": {
        "load": lambda seasons, _st: nflreadpy.load_injuries(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["gsis_id", "season", "week"],
        "cursor_field": None,
    },
    "draft_picks": {
        "load": lambda seasons, _st: nflreadpy.load_draft_picks(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["pfr_player_id", "season"],
        "cursor_field": None,
    },
    "combine": {
        "load": lambda seasons, _st: nflreadpy.load_combine(seasons=seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["pfr_id", "season"],
        "cursor_field": None,
    },
}


# ---------------------------------------------------------------------------
# LakeflowConnect interface
# ---------------------------------------------------------------------------

class LakeflowConnect:
    """nflverse connector for Lakeflow Connect."""

    def __init__(self, options: dict[str, str]) -> None:
        self._seasons = _parse_seasons(options)
        self._season_type = _parse_season_type(options)

    # -- Discovery -----------------------------------------------------------

    def list_tables(self) -> list[str]:
        return list(TABLE_REGISTRY.keys())

    def get_table_schema(self, table_name: str, table_options: dict[str, str]) -> StructType:
        if table_name == "play_by_play":
            sample = nflreadpy.load_pbp(seasons=self._seasons[:1])
        else:
            entry = TABLE_REGISTRY[table_name]
            sample = entry["load"](self._seasons[:1], self._season_type)
        return _infer_spark_schema(sample)

    def read_table_metadata(self, table_name: str, table_options: dict[str, str]) -> dict:
        entry = TABLE_REGISTRY[table_name]
        return {
            "primary_keys": entry["primary_keys"],
            "cursor_field": entry["cursor_field"],
            "ingestion_type": entry["ingestion_type"],
        }

    # -- Data reads ----------------------------------------------------------

    def read_table(
        self,
        table_name: str,
        start_offset: dict,
        table_options: dict[str, str],
    ) -> tuple[Iterator[dict], dict]:
        if table_name == "play_by_play":
            return self._read_pbp(start_offset, table_options)

        entry = TABLE_REGISTRY[table_name]
        df = entry["load"](self._seasons, self._season_type)
        return iter(_df_to_dicts(df)), {"completed": True}

    def _read_pbp(
        self,
        start_offset: dict,
        table_options: dict[str, str],
    ) -> tuple[Iterator[dict], dict]:
        """Load play-by-play with optional incremental mode."""
        incremental = table_options.get("pbp_incremental", "false").lower() == "true"
        initial_done = start_offset.get("initial_load_complete", False)

        if incremental and initial_done:
            load_seasons = [max(self._seasons)]
        else:
            load_seasons = self._seasons

        df = nflreadpy.load_pbp(seasons=load_seasons)
        next_offset = {
            "initial_load_complete": True,
            "latest_season": max(self._seasons),
        }
        return iter(_df_to_dicts(df)), next_offset

    def read_table_deletes(
        self,
        table_name: str,
        start_offset: dict,
        table_options: dict[str, str],
    ) -> tuple[Iterator[dict], dict]:
        raise NotImplementedError("read_table_deletes not supported for nflverse connector")
