# NFLverse Fantasy API Reference

The `nfl.nflverse_fantasy` module ingests broad NFL datasets from the nflverse project (play-by-play, schedules, rosters, participation data, etc.) and optionally persists them to Iceberg or Unity Catalog.

## Quick Import

```python
from nfl.nflverse_fantasy import (
    NflverseApiClient,
    PipelineConfig,
    PipelineRunResult,
    run_pipeline,
)
```

---

## Pipeline

### `run_pipeline`

```python
run_pipeline(
    config: PipelineConfig | None = None,
    api_client: NflverseApiClient | None = None,
) -> PipelineRunResult
```

Main entry point. Downloads nflverse datasets, applies transforms, validates schemas, and optionally persists data.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `config` | `PipelineConfig \| None` | Pipeline options; defaults apply when `None` |
| `api_client` | `NflverseApiClient \| None` | Override the default client |

---

### `PipelineConfig`

| Field | Type | Default | Description |
|---|---|---|---|
| `storage_target` | `str` | `"none"` | `"none"`, `"polars"`, `"iceberg"`, or `"both"` |
| `polars_output_dir` | `str \| None` | `None` | Directory for local Parquet output |
| `polars_file_format` | `str` | `"parquet"` | Output format for local files |
| `iceberg_dry_run` | `bool` | `True` | Dry-run mode for Iceberg writes |
| `iceberg_idempotency_store` | `str \| None` | `None` | Write-log path |
| `validate_contracts` | `bool` | `True` | Validate output schemas |
| `enabled_entities` | `list[str] \| None` | `None` | Limit ingestion to a named subset of entities |
| `standardization_enabled` | `bool` | `False` | Run entity standardization after ingestion |
| `standardization_config` | `StandardizationConfig \| None` | `None` | Override standardization defaults |

Use `enabled_entities` to narrow ingestion for speed. For example, to ingest only schedules and rosters:

```python
config = PipelineConfig(enabled_entities=["schedules", "rosters"])
```

---

### `PipelineRunResult`

| Field | Type | Description |
|---|---|---|
| `frames` | `dict[str, pl.DataFrame]` | Named Polars DataFrames |
| `polars_outputs` | `list[str]` | Paths to written Polars files |
| `iceberg_plan` | `list \| None` | Iceberg write plan (on dry-run) |

---

## API Client

### `NflverseApiClient`

Downloads raw nflverse datasets (hosted on GitHub Releases and S3). Handles caching and schema coercion.

```python
client = NflverseApiClient()
```

Key methods:

| Method | Description |
|---|---|
| `fetch_pbp(seasons)` | Play-by-play data for one or more seasons |
| `fetch_schedules(seasons)` | Game schedules and results |
| `fetch_rosters(seasons)` | Weekly player rosters |
| `fetch_player_stats(seasons)` | Aggregated player statistics |
| `fetch_participation(seasons)` | Snap count and participation data |
| `fetch_injuries(seasons)` | Injury report data |
| `fetch_draft_picks(seasons)` | Historical draft picks |
| `fetch_combine(seasons)` | NFL Combine measurements |
| `fetch_contracts(seasons)` | Player contract data |
| `fetch_depth_charts(seasons)` | Depth chart snapshots |
| `fetch_officials(seasons)` | Game officials |
| `fetch_nextgen_stats(seasons, stat_type)` | NFL NextGen Stats (passing, rushing, receiving) |

---

## Available Entities

The following entity names can be passed to `enabled_entities`:

| Entity | Description |
|---|---|
| `schedules` | Game schedule and result data |
| `rosters` | Weekly roster snapshots |
| `player_stats` | Aggregated season and game stats |
| `pbp` | Play-by-play records |
| `participation` | Snap count and participation |
| `injuries` | Weekly injury reports |
| `draft_picks` | Historical draft selections |
| `combine` | Combine measurements and scores |
| `contracts` | Player contract details |
| `depth_charts` | Weekly depth chart positions |
| `officials` | Game officials and crews |
| `nextgen_stats_passing` | NextGen passing metrics |
| `nextgen_stats_rushing` | NextGen rushing metrics |
| `nextgen_stats_receiving` | NextGen receiving metrics |

---

## Storage

### Local Polars

```python
config = PipelineConfig(
    storage_target="polars",
    polars_output_dir="./output/nflverse",
)
result = run_pipeline(config=config)
print(result.polars_outputs)
```

### Iceberg (Dry Run)

```python
config = PipelineConfig(
    storage_target="iceberg",
    iceberg_dry_run=True,
    iceberg_idempotency_store="./iceberg_write_log.json",
)
result = run_pipeline(config=config)
print(result.iceberg_plan)
```

---

## Notes

- nflverse data is sourced from public GitHub releases; no authentication is required.
- The pipeline is designed for wide ingestion followed by optional narrowing via `enabled_entities`.
- For integration testing, use `storage_target="none"` to validate transforms without any I/O.
