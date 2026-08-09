# nflverse Community Connector

A Lakeflow Connect community connector that ingests NFL data from
[nflverse](https://github.com/nflverse/nflreadpy) into Databricks.

## Prerequisites

- `nflreadpy` installed on your pipeline cluster:
  Add `nflreadpy` to your pipeline's **Libraries** configuration.
- No authentication required — nflverse data is publicly hosted on GitHub releases.

## Configuration Parameters

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `seasons` | Yes | — | Comma-separated NFL seasons to ingest. Example: `2022,2023,2024` |
| `season_type` | No | `REG` | Season type for seasonal stats: `REG`, `POST`, or `REG_POST` |

## Available Tables

| Table | Primary Keys | Description |
| --- | --- | --- |
| `player_stats_weekly` | player_id, season, week, season_type | Weekly player stats (QB/RB/WR/TE/K) |
| `player_stats_seasonal` | player_id, season, season_type | Season-level aggregated player stats |
| `schedules` | game_id | Game schedules with results and metadata |
| `rosters` | player_id, season, week | Weekly roster + player bio |
| `teams` | team_abbr | Team metadata, colors, and logos |
| `snap_counts` | pfr_player_id, season, week | Offensive/defensive snaps per game |
| `depth_charts` | gsis_id, season, week, position, depth_position | Weekly depth chart positions |
| `injuries` | gsis_id, season, week | Weekly injury report designations |
| `draft_picks` | pfr_player_id, season | Historical draft picks |
| `combine` | pfr_id, season | NFL Combine measurables |

All tables use `snapshot` ingestion — the full dataset is reloaded on each pipeline run.

## Deploying in Your Workspace

1. Point your Lakeflow Connect pipeline at this directory (or a GitHub repo containing it).
2. Databricks clones the source at runtime and executes `connector.py`.
3. Specify `seasons` and optionally `season_type` in the pipeline configuration.

## Building the Deployment Artifact

If contributing to the [Lakeflow Community Connectors repo](https://github.com/databrickslabs/lakeflow-connect-community),
run the merge script from the repo root to produce a single-file artifact:

```bash
python tools/scripts/merge_python_source.py --connector nflverse
```

This outputs `dist/nflverse/connector.py`.

## Notes

- `play_by_play` is intentionally excluded from snapshot tables — it's large
  and uses CDC (incremental) mode instead.
- Data freshness depends on nflverse release cadence (typically weekly during season).
