"""NFL-scoped FantasyPros data contracts."""

from __future__ import annotations

NFL_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
	"fp_current_adp": {
		"required": (
			"fp_player_id",
			"full_name",
			"position",
			"team",
			"season",
			"rank",
			"position_rank",
			"adp",
			"effective_date",
		),
		"optional": (
			"adp_espn",
			"adp_sleeper",
			"adp_cbs",
			"adp_nfl",
			"adp_rtsports",
			"adp_fantrax",
			"adp_realtime",
			"adp_formatted",
			"high",
			"low",
			"stdev",
			"bye_week",
		),
		"primary_key": ("season", "fp_player_id"),
	}
}
