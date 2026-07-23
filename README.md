# yahoo_fantasy

Unified Yahoo Fantasy library for extraction, normalization, Polars transforms, and optional Iceberg persistence.

## Status
- Milestones A-F complete
- Library-only architecture (no CLI/GUI)
- Python 3.12+

## Zensical Documentation
- Package guide: `docs/ZENSICAL_DOCUMENTATION.md`

## Install

```powershell
C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pip install -e .
```

## Quickstart

```python
from pathlib import Path
import os

from nfl.yahoo_fantasy import build_oauth_session, PipelineConfig, run_pipeline

oauth = build_oauth_session(
    client_id=os.environ["YAHOO_CLIENT_ID"],
    client_secret=os.environ["YAHOO_CLIENT_SECRET"],
    redirect_uri=os.environ["YAHOO_REDIRECT_URI"],
    token_path=Path(".yahoo_token.json"),
    auth_code=None,  # Provide value if first-time auth and no cached token exists
    open_browser=False,
)

result = run_pipeline(
    league_key="461.l.717896",
    sport="nfl",
    oauth_session=oauth,
    config=PipelineConfig(
        storage_target="both",
        polars_output_dir="./output/polars",
        iceberg_dry_run=True,
    ),
)

print(result.frames.keys())
print(result.polars_outputs)
```

## Persistence Defaults
- Iceberg catalog type: `sql`
- Iceberg namespaces:
  - NFL: `yhnfl`
  - NBA: `ynbna`

## Warehouse Query Quickstart

Use the query layer to discover and load existing Iceberg tables as Polars DataFrames.

```python
from nfl.yahoo_fantasy import YahooWarehouseClient

client = YahooWarehouseClient.from_project_root()
report = client.ensure_registered()
print(report)

print(client.list_namespaces())
print(client.list_tables("yahoo_common"))

league_df = client.load_table("yahoo_common.league")
team_df = client.maybe_load("yahoo_common.team")
```

You can also run reusable analytics helpers that mirror the notebook examples:

```python
from nfl.yahoo_fantasy import league_team_info, weekly_team_points

league_team = league_team_info(league_df=league_df, team_df=team_df)

stats_df = client.maybe_load("yhnfl.player_stats_weekly")
roster_df = client.maybe_load("yhnfl.roster_entries")
matchups_df = client.maybe_load("yhnfl.matchups")

weekly_points, points_source = weekly_team_points(stats_df, roster_df, matchups_df)
print(points_source)
print(weekly_points)
```

## Testing

```powershell
C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q
```

## Tracking
Implementation plan and milestone log are in `YAHOO_INTEGRATION_BLUEPRINT.md`.

## fantasypros_fantasy Quickstart

```python
from datetime import date

from nfl.fantasypros_fantasy import PipelineConfig, run_pipeline

yahoo_players = [
    {
        "yahoo_player_id": 1001,
        "full_name": "Justin Jefferson",
        "first_name": "Justin",
        "last_name": "Jefferson",
        "display_position": "WR",
    }
]

result = run_pipeline(
    season=2025,
    yahoo_players=yahoo_players,
    config=PipelineConfig(
        storage_target="both",
        effective_date=date(2026, 7, 18),
        polars_output_dir="./output/fantasypros_polars",
        iceberg_dry_run=True,
    ),
)

print(result.frames.keys())
print(result.polars_outputs)
```

FantasyPros blueprint: `FANTASY_PROS_INTEGRATION_BLUEPRINT.md`

FantasyPros notebook migration guide: `FANTASY_PROS_NOTEBOOK_MIGRATION.md`

## entity_standardization Quickstart

```python
from nfl.entity_standardization import EntityStandardizer, StandardizationConfig

records = [
    {
        "source_system": "fantasypros",
        "source_entity_id": "austin-ekeler",
        "raw_player_name": "Austin Ekeler",
        "raw_team_name": "San Diego",
        "raw_position": "HB",
        "season": 2025,
    },
    {
        "source_system": "yahoo",
        "source_entity_id": "unknown_player",
        "raw_player_name": "Mystery Name",
        "raw_team_name": "LAC",
        "raw_position": "WR",
        "season": 2025,
    },
]

standardizer = EntityStandardizer(
    config=StandardizationConfig(
        auto_accept_thresholds={
            "default": {
                "player": 0.97,
                "team": 0.995,
                "position": 1.0,
            }
        },
        persist_tables=True,
        polars_output_dir="./output/standardization",
        iceberg_enabled=True,
        iceberg_dry_run=True,
    )
)

result = standardizer.standardize_batch(records)

# API outputs
print(result.standardized_records)

# Persisted table outputs (Polars + optional Iceberg dry run results)
print(result.tables.keys())
print(result.polars_outputs)
print(result.iceberg_outputs)
```

### Queue Workflow
- `std_match_queue`: all review candidates with status and assignment fields.
- `std_match_queue_open`: unresolved worklist (`new`, `in_review`).
- `std_match_queue_history`: resolved items with audit trail.
- `std_manual_overrides`: approved fixes applied in subsequent runs.
- `std_rescued_records`: unresolved source payloads for replay after manual resolution.

### Position and Team Rules
- Positions are standardized to: `QB`, `RB`, `WR`, `TE`, `DST`, `K`.
- Position aliases map `FB` and `HB` to `RB`.
- Legacy team aliases map to current team codes (for example, `San Diego` -> `LAC`).

Entity standardization blueprint: `ENTITY_STANDARDIZATION_BLUEPRINT.md`

## nflverse_fantasy Quickstart

```python
from nfl.nflverse_fantasy import PipelineConfig, run_pipeline

result = run_pipeline(
    config=PipelineConfig(
        seasons=[2024],
        enabled_entities=["players", "schedules", "player_stats", "pbp"],
        storage_target="both",
        polars_output_dir="./output/nflverse_polars",
        iceberg_dry_run=True,
        standardization_enabled=True,
    )
)

print(result.frames.keys())
print(result.polars_outputs)
print(result.iceberg_outputs)
```

NFLverse blueprint: `blueprints/NFLVERSE_INGESTION_BLUEPRINT.md`

