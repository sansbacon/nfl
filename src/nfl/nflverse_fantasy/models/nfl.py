"""NFL-only entity contracts for nflreadpy wrapper datasets."""

from __future__ import annotations

_DATASETS: tuple[str, ...] = (
    "pbp",
    "player_stats",
    "team_stats",
    "schedules",
    "players",
    "rosters",
    "rosters_weekly",
    "snap_counts",
    "nextgen_stats",
    "ftn_charting",
    "participation",
    "draft_picks",
    "injuries",
    "contracts",
    "officials",
    "combine",
    "depth_charts",
    "trades",
    "ff_playerids",
    "ff_rankings",
    "ff_opportunity",
)

NFL_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
    name: {
        "required": ("_record_hash", "_dataset", "_loaded_at"),
        "optional": (),
        "primary_key": ("_record_hash",),
    }
    for name in _DATASETS
}
