"""nflverse Community Connector for Lakeflow Connect.

Ingests NFL data from nflverse via the nfl_data_py package.
See: https://github.com/nflverse/nfl_data_py

Required pip install: nfl_data_py

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

import nfl_data_py as nfl
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


def _df_to_dicts(df) -> list[dict]:
    """Convert a pandas DataFrame to a list of JSON-serialisable dicts."""
    return df.where(df.notna(), other=None).to_dict(orient="records")


def _infer_spark_schema(df) -> StructType:
    """Build a StructType from pandas dtypes (best-effort)."""
    type_map = {
        "int64": IntegerType(),
        "int32": IntegerType(),
        "float64": DoubleType(),
        "float32": DoubleType(),
    }
    fields = []
    for col, dtype in df.dtypes.items():
        spark_type = type_map.get(str(dtype), StringType())
        fields.append(StructField(str(col), spark_type, nullable=True))
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
        "load": lambda seasons, _st: nfl.import_weekly_data(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["player_id", "season", "week", "season_type"],
        "cursor_field": None,
    },
    "player_stats_seasonal": {
        "load": lambda seasons, st: nfl.import_seasonal_data(seasons, season_type=st),
        "ingestion_type": "snapshot",
        "primary_keys": ["player_id", "season", "season_type"],
        "cursor_field": None,
    },
    "schedules": {
        "load": lambda seasons, _st: nfl.import_schedules(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["game_id"],
        "cursor_field": None,
    },
    "rosters": {
        "load": lambda seasons, _st: nfl.import_rosters(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["player_id", "season", "week"],
        "cursor_field": None,
    },
    "teams": {
        "load": lambda _seasons, _st: nfl.import_team_desc(),
        "ingestion_type": "snapshot",
        "primary_keys": ["team_abbr"],
        "cursor_field": None,
    },
    "snap_counts": {
        "load": lambda seasons, _st: nfl.import_snap_counts(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["pfr_player_id", "season", "week"],
        "cursor_field": None,
    },
    "depth_charts": {
        "load": lambda seasons, _st: nfl.import_depth_charts(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["gsis_id", "season", "week", "position", "depth_position"],
        "cursor_field": None,
    },
    "injuries": {
        "load": lambda seasons, _st: nfl.import_injuries(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["gsis_id", "season", "week"],
        "cursor_field": None,
    },
    "draft_picks": {
        "load": lambda seasons, _st: nfl.import_draft_picks(seasons),
        "ingestion_type": "snapshot",
        "primary_keys": ["pfr_player_id", "season"],
        "cursor_field": None,
    },
    "combine": {
        "load": lambda seasons, _st: nfl.import_combine_data(seasons),
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
            sample = nfl.import_pbp_data(self._seasons[:1])
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

        df = nfl.import_pbp_data(load_seasons)
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
