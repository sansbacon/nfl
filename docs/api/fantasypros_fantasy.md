# FantasyPros Fantasy API Reference

The `nfl.fantasypros_fantasy` module fetches and normalizes FantasyPros ADP rankings, optionally builds a Yahoo↔FantasyPros player crosswalk, and persists data to Unity Catalog or Iceberg.

## Quick Import

```python
from nfl.fantasypros_fantasy import (
    FantasyProsApiClient,
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
    season: int,
    sport: str = "nfl",
    config: PipelineConfig | None = None,
    api_client: FantasyProsApiClient | None = None,
    yahoo_players: list[dict] | None = None,
) -> PipelineRunResult
```

Main entry point. Fetches FantasyPros ADP data for the given season, optionally matches players against a Yahoo player list, and persists results.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `season` | `int` | NFL season year, e.g. `2025` |
| `sport` | `str` | Sport code; currently `"nfl"` |
| `config` | `PipelineConfig \| None` | Pipeline options |
| `api_client` | `FantasyProsApiClient \| None` | Override the default client |
| `yahoo_players` | `list[dict] \| None` | Yahoo player records for crosswalk matching |

---

### `PipelineConfig`

| Field | Type | Default | Description |
|---|---|---|---|
| `storage_target` | `str` | `"none"` | `"none"`, `"polars"`, `"iceberg"`, `"unity_catalog"`, or `"both"` |
| `polars_output_dir` | `str \| None` | `None` | Directory for local Parquet output |
| `polars_file_format` | `str` | `"parquet"` | Output format for local files |
| `iceberg_dry_run` | `bool` | `True` | Dry-run mode for Iceberg writes |
| `validate_contracts` | `bool` | `True` | Validate output schemas |
| `uc_table_config` | `FantasyProsUCTableConfig \| None` | `None` | Unity Catalog target settings |
| `uc_dry_run` | `bool` | `True` | Dry-run mode for UC writes |

---

### `PipelineRunResult`

| Field | Type | Description |
|---|---|---|
| `frames` | `dict[str, pl.DataFrame]` | Named Polars DataFrames produced by the pipeline |
| `polars_outputs` | `list[str]` | Paths to written Polars files |
| `iceberg_plan` | `list \| None` | Iceberg write plan (on dry-run) |

---

## API Client

### `FantasyProsApiClient`

Handles scraping and parsing of FantasyPros ADP data, including CSV volume parsing for Unity Catalog workflows.

```python
client = FantasyProsApiClient(validate_contracts=True)
```

Key methods:

| Method | Description |
|---|---|
| `fetch_adp(season, sport)` | Fetch current ADP rankings from FantasyPros |
| `parse_adp_volume_csv(path, season)` | Parse a FantasyPros ADP CSV file from a UC Volume path |

---

## Matching

### `build_fp_yahoo_crosswalk`

```python
from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk

# Function signature
def build_fp_yahoo_crosswalk(
    fp_players: list[dict],
    yahoo_players: list[dict],
) -> list[dict]: ...

# Example call
crosswalk = build_fp_yahoo_crosswalk(
    fp_players=fp_players,
    yahoo_players=yahoo_players,
)
```

Matches FantasyPros players to Yahoo players using name normalization and fuzzy matching. Returns a list of crosswalk records.

Each record includes:

| Field | Description |
|---|---|
| `fp_player_id` | FantasyPros player identifier |
| `yahoo_player_id` | Matched Yahoo player identifier |
| `fp_full_name` | FantasyPros display name |
| `yahoo_full_name` | Yahoo display name |
| `match_method` | `"exact"`, `"fuzzy"`, or `"manual"` |
| `match_score` | Fuzzy match confidence score (0–1) |

### `fp_adp_records_to_fp_players`

```python
from nfl.fantasypros_fantasy import fp_adp_records_to_fp_players

fp_players = fp_adp_records_to_fp_players(fp_adp_records: list[dict]) -> list[dict]
```

Converts raw FP ADP table rows (as stored in UC) to the normalized `fp_player` format expected by `build_fp_yahoo_crosswalk`.

---

## Unity Catalog Storage

### `FantasyProsUCTableConfig`

```python
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig

config = FantasyProsUCTableConfig(
    catalog="nfl",
    schema="fp",
    write_mode="overwrite",  # overwrite | append | merge
)
```

### `persist_fp_to_uc_tables`

```python
from nfl.fantasypros_fantasy.storage.unity_catalog import persist_fp_to_uc_tables

results = persist_fp_to_uc_tables(
    frames={"fp_adp": adp_df},
    config=uc_config,
    dry_run=False,
)
```

---

## Output Tables

| Table | Description |
|---|---|
| `fp_adp` | ADP rankings per player per season |
| `nfl_fp_current_adp` | Current-season ADP snapshot (materialized) |
| `nfl_fp_yahoo_player_map` | Yahoo↔FantasyPros player crosswalk |

See the [FantasyPros example](../examples/load_fantasypros_adp.md) and [matching example](../examples/match_yahoo_fantasypros.md) for end-to-end usage.
