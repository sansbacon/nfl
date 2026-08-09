# nfl

Unified NFL fantasy football data library: extraction, normalization, and persistence across Yahoo, FantasyPros, ESPN, Sleeper, and NFLverse sources.

## Overview

`nfl` is a Python library for building fantasy football data pipelines. It provides a consistent interface for fetching data from multiple sources, normalizing player and team names across those sources, and persisting the results as Polars parquet files, Apache Iceberg tables, or Unity Catalog Delta tables.

**Key capabilities:**

- **Multi-source ingestion** – Yahoo Fantasy (OAuth), FantasyPros (scraping/API), ESPN (public API), Sleeper (public API), NFLverse (nflreadpy)
- **Entity standardization** – fuzzy-match player names, team codes, and positions across sources; queue unresolved matches for manual review
- **Flexible persistence** – write to local parquet files, a local Iceberg catalog (SQLite), or Databricks Unity Catalog
- **Library-only** – no CLI or GUI; import and compose pipelines in Python scripts or notebooks

## Status

- Python 3.12+
- Library-only architecture (no CLI/GUI)
- All major data-source integrations implemented (Yahoo, FantasyPros, ESPN, Sleeper, NFLverse)
- Entity standardization pipeline with review queue

## Project Layout

```
src/nfl/
├── common/                   # Shared utilities (crosswalk, matching, storage)
│   ├── crosswalk.py          # load_canonical_crosswalk()
│   ├── matching.py           # normalize_name()
│   └── storage/
│       ├── polars.py         # persist_with_polars()
│       ├── unity_catalog.py  # UCTableConfig, persist_to_uc_tables()
│       └── iceberg.py        # IcebergCatalogConfig, persist_to_iceberg()
├── yahoo_fantasy/            # Yahoo Fantasy OAuth extraction and transforms
├── fantasypros_fantasy/      # FantasyPros ADP/rankings scraping and transforms
├── espn_fantasy/             # ESPN public API extraction and transforms
├── sleeper_fantasy/          # Sleeper public API extraction and transforms
├── nflverse_fantasy/         # NFLverse data ingestion (nflreadpy)
└── entity_standardization/   # Cross-source entity resolution

tests/                        # pytest test suite
examples/                     # Example scripts and Jupyter notebooks
scripts/                      # CLI helper scripts (load_data, rebuild_catalog)
blueprints/                   # Architecture and design documents
```

## Install

```bash
# Install in editable mode (recommended for development)
pip install -e ".[dev]"

# Install with Apache Iceberg support
pip install -e ".[iceberg]"
```

## Environment Variables

Copy your credentials into a `.env` file or export them in your shell. The Yahoo integration is the only source that requires OAuth credentials.

| Variable | Required for |
|---|---|
| `YAHOO_CLIENT_ID` | Yahoo Fantasy |
| `YAHOO_CLIENT_SECRET` | Yahoo Fantasy |
| `YAHOO_REDIRECT_URI` | Yahoo Fantasy |

## Quickstart by Source

### Yahoo Fantasy

```python
import os
from pathlib import Path

from nfl.yahoo_fantasy import build_oauth_session, PipelineConfig, run_pipeline

oauth = build_oauth_session(
    client_id=os.environ["YAHOO_CLIENT_ID"],
    client_secret=os.environ["YAHOO_CLIENT_SECRET"],
    redirect_uri=os.environ["YAHOO_REDIRECT_URI"],
    token_path=Path(".yahoo_token.json"),
    auth_code=None,  # Provide on first-time auth; omit once a cached token exists
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

#### Warehouse Query Client

Use `YahooWarehouseClient` to discover and load existing Iceberg tables as Polars DataFrames:

```python
from nfl.yahoo_fantasy import YahooWarehouseClient, league_team_info, weekly_team_points

client = YahooWarehouseClient.from_project_root()
client.ensure_registered()

league_df = client.load_table("yahoo_common.league")
team_df   = client.maybe_load("yahoo_common.team")
stats_df  = client.maybe_load("yhnfl.player_stats_weekly")
roster_df = client.maybe_load("yhnfl.roster_entries")
matchups_df = client.maybe_load("yhnfl.matchups")

league_team   = league_team_info(league_df=league_df, team_df=team_df)
weekly_points, points_source = weekly_team_points(stats_df, roster_df, matchups_df)
```

### FantasyPros

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
        effective_date=date(2025, 8, 1),
        polars_output_dir="./output/fantasypros_polars",
        iceberg_dry_run=True,
    ),
)

print(result.frames.keys())
print(result.polars_outputs)
```

### NFLverse

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

### Entity Standardization

Resolve player names, team codes, and positions across sources. Unresolved matches are placed in a review queue.

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
        auto_accept_thresholds={"default": {"player": 0.97, "team": 0.995, "position": 1.0}},
        persist_tables=True,
        polars_output_dir="./output/standardization",
        iceberg_enabled=True,
        iceberg_dry_run=True,
    )
)

result = standardizer.standardize_batch(records)

print(result.standardized_records)
print(result.tables.keys())
print(result.polars_outputs)
print(result.iceberg_outputs)
```

**Standardization rules:**
- Positions are normalized to: `QB`, `RB`, `WR`, `TE`, `DST`, `K` (aliases `FB`/`HB` → `RB`).
- Legacy team codes are mapped to current codes (for example, `San Diego` → `LAC`).

**Review queue tables:**

| Table | Description |
|---|---|
| `std_match_queue` | All review candidates with status and assignment fields |
| `std_match_queue_open` | Unresolved worklist (`new`, `in_review`) |
| `std_match_queue_history` | Resolved items with audit trail |
| `std_manual_overrides` | Approved fixes applied in subsequent runs |
| `std_rescued_records` | Unresolved source payloads queued for replay |

## Persistence

Each pipeline accepts a `storage_target` that controls where data is written:

| `storage_target` | Where data is written |
|---|---|
| `"polars"` | Local parquet files (path set by `polars_output_dir`) |
| `"iceberg"` | Local Iceberg catalog (SQLite) |
| `"unity_catalog"` | Databricks Unity Catalog Delta tables (`nfl.*` catalog) |
| `"both"` | Polars parquet **and** Iceberg |

Iceberg namespaces for Yahoo data: `yhnfl` (NFL), `ynba` (NBA).

Set `iceberg_dry_run=True` to validate the pipeline without writing to Iceberg.

## Dashboards

| Dashboard | Description |
|-----------|-------------|
| `yh_auction_myleague` | Yahoo auction values analysis for personal leagues. Published Lakeview dashboard reading from `nfl.yh.auction_values_myleague`. |

## Lakeflow Connector

The `nflverse_connector/` directory contains a Lakeflow Connect community connector
that ingests nflverse data (player stats, schedules, rosters, snap counts, etc.)
directly into Unity Catalog. See `nflverse_connector/README.md` for deployment.

## Testing

```bash
# Run all unit tests
pytest

# Exclude slow or integration tests
pytest -m "not integration"

# Run with coverage report
pytest --cov --cov-report=term-missing
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code style guidelines, and how to run the full dev toolchain (ruff, mypy, pre-commit).

## Architecture

Design documents and blueprints are in the `blueprints/` directory:

- `blueprints/YAHOO_INTEGRATION_BLUEPRINT.md` – Yahoo Fantasy integration plan
- `blueprints/FANTASY_PROS_INTEGRATION_BLUEPRINT.md` – FantasyPros integration plan
- `blueprints/ENTITY_STANDARDIZATION_BLUEPRINT.md` – Entity standardization design
- `blueprints/NFLVERSE_INGESTION_BLUEPRINT.md` – NFLverse ingestion design

## License

MIT

