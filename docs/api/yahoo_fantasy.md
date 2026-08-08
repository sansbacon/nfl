# Yahoo Fantasy API Reference

The `nfl.yahoo_fantasy` module provides OAuth-authenticated access to the Yahoo Fantasy Sports API, Polars-based data transforms, optional Unity Catalog / Iceberg persistence, and query helpers for persisted data.

## Quick Import

```python
from nfl.yahoo_fantasy import (
    build_oauth_session,
    PipelineConfig,
    PipelineRunResult,
    run_pipeline,
    YahooApiClient,
)
```

---

## Authentication

### `build_oauth_session`

```python
build_oauth_session(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    token_path: Path,
    auth_code: str | None = None,
    open_browser: bool = False,
) -> OAuth2Session
```

Builds and returns an authenticated `requests_oauthlib.OAuth2Session`.

- On the first run, provide `auth_code` obtained from Yahoo's OAuth flow.
- On subsequent runs, the cached token is loaded automatically from `token_path`.
- Set `open_browser=True` to have the library open the authorization URL automatically.

### `load_token`

```python
load_token(token_path: Path) -> dict
```

Loads and returns the raw token dictionary from a cached token file.

---

## Pipeline

### `run_pipeline`

```python
run_pipeline(
    league_key: str,
    sport: str,
    oauth_session: OAuth2Session | None = None,
    config: PipelineConfig | None = None,
    api_client: YahooApiClient | None = None,
) -> PipelineRunResult
```

Main entry point. Ingests all Yahoo Fantasy data for the given league and season, optionally persists it, and returns a `PipelineRunResult`.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `league_key` | `str` | Yahoo league key, e.g. `"461.l.717896"` |
| `sport` | `str` | `"nfl"` or `"nba"` |
| `oauth_session` | `OAuth2Session \| None` | Required unless `api_client` is provided |
| `config` | `PipelineConfig \| None` | Pipeline options; defaults apply when `None` |
| `api_client` | `YahooApiClient \| None` | Override the default API client |

---

### `PipelineConfig`

Controls pipeline behavior, storage target, and optional features.

| Field | Type | Default | Description |
|---|---|---|---|
| `storage_target` | `str` | `"none"` | `"none"`, `"polars"`, `"iceberg"`, `"unity_catalog"`, or `"both"` |
| `polars_output_dir` | `str \| None` | `None` | Directory for local Parquet output |
| `polars_file_format` | `str` | `"parquet"` | Output format for local files |
| `iceberg_dry_run` | `bool` | `True` | When `True`, plans writes without executing them |
| `iceberg_idempotency_store` | `str \| None` | `None` | Path to the write-log used for idempotency |
| `use_cache` | `bool` | `False` | Use locally cached API responses |
| `validate_contracts` | `bool` | `True` | Validate output schemas at pipeline boundaries |
| `start_week` | `int` | `1` | First week to ingest |
| `end_week` | `int` | `17` | Last week to ingest |
| `include_nfl_unrostered_player_stats` | `bool` | `True` | Include stats for players not on a roster |
| `standardization_enabled` | `bool` | `False` | Run entity standardization after ingestion |
| `standardization_config` | `StandardizationConfig \| None` | `None` | Override standardization defaults |
| `uc_table_config` | `YahooUCTableConfig \| None` | `None` | Unity Catalog target settings |
| `uc_dry_run` | `bool` | `True` | Dry-run mode for UC writes |
| `diagnostics` | `PipelineDiagnosticsConfig \| None` | `None` | Diagnostic capture settings |

---

### `PipelineRunResult`

Returned by `run_pipeline`. Contains all output data and optional diagnostics.

| Field | Type | Description |
|---|---|---|
| `frames` | `dict[str, pl.DataFrame]` | Named Polars DataFrames produced by the pipeline |
| `polars_outputs` | `list[str]` | Paths to written Polars files (if applicable) |
| `iceberg_plan` | `list \| None` | Iceberg write plan (populated on dry-run) |
| `diagnostics` | `PipelineDiagnosticsResult \| None` | Timing and stage summaries |

---

## API Client

### `YahooApiClient`

Low-level client for the Yahoo Fantasy Sports REST API. Wraps authenticated session calls and handles pagination and retries.

```python
client = YahooApiClient(oauth_session=oauth_session)
```

Key methods:

| Method | Description |
|---|---|
| `get_league(league_key)` | Fetch league metadata |
| `get_teams(league_key)` | Fetch all teams in a league |
| `get_players(league_key, ...)` | Fetch player list |
| `get_roster(team_key, week)` | Fetch roster for a team/week |
| `get_player_stats(player_keys, week)` | Fetch weekly stats for a set of players |
| `get_matchups(league_key, week)` | Fetch matchup results |
| `get_draft_results(league_key)` | Fetch draft picks and auction prices |
| `get_standings(league_key)` | Fetch current standings |

---

## Query APIs

Use these functions to query persisted data from a local Iceberg warehouse or Unity Catalog.

### Warehouse Client

```python
from nfl.yahoo_fantasy.warehouse import YahooWarehouseClient

wc = YahooWarehouseClient(warehouse_path="./iceberg_warehouse")
```

### Query Functions

Import from `nfl.yahoo_fantasy.queries`:

| Function | Description |
|---|---|
| `league_team_info(league_df, team_df)` | Combined league and team metadata |
| `standings_summary(standings_df, team_df)` | Human-readable standings table |
| `weekly_team_points(team_df, player_stats_df, roster_entries_df)` | Weekly points by team |
| `build_player_weekly_points(player_stats_df, player_df)` | Player-level weekly scoring |
| `position_weekly_points(player_stats_df, player_df)` | Aggregated scoring by position |
| `team_position_weekly_points(...)` | Scoring by team and position per week |
| `average_scoring_by_position_by_team(...)` | Season averages by team and position |
| `latest_roster_snapshot(roster_entries_df, player_df)` | Most recent roster composition |
| `scoring_quality_by_week(player_stats_df)` | Week-level scoring quality metrics |
| `player_points_health(player_stats_df)` | Data completeness check for player stats |
| `unified_draft_price_analysis(draft_df, player_df, fp_adp_df, fp_crosswalk_df)` | Draft value versus FP ADP |

---

## Unity Catalog Storage

### `YahooUCTableConfig`

```python
from nfl.yahoo_fantasy.storage.unity_catalog import YahooUCTableConfig

config = YahooUCTableConfig(
    catalog="nfl",
    nfl_schema="yh",
    nba_schema="yh_nba",
    common_schema="yh",
    write_mode="overwrite",  # overwrite | append | merge
)
```

### `persist_yahoo_to_uc_tables`

```python
from nfl.yahoo_fantasy.storage.unity_catalog import persist_yahoo_to_uc_tables

results = persist_yahoo_to_uc_tables(
    frames=result.frames,
    config=uc_table_config,
    dry_run=False,
)
```

---

## Output Tables

When `storage_target` includes `"unity_catalog"` or `"iceberg"`, the pipeline writes these tables (prefixed with the sport):

| Table | Description |
|---|---|
| `league` | League metadata |
| `team` | Team roster entries |
| `player` | Player dimension |
| `player_deduped` | Deduplicated player dimension (one row per player ID) |
| `player_stats_weekly` | Weekly fantasy points per player |
| `roster_entries` | Weekly roster snapshots |
| `matchups` | Weekly head-to-head matchup results |
| `draft_pick` | Draft picks with auction prices |
| `standings` | Current season standings |
| `transactions` | Waiver wire and trade transactions |

See the [Practical Examples](../examples/load_yahoo_data.md) for end-to-end usage.
