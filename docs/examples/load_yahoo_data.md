# Example: Load Yahoo Fantasy Data

This example runs the Yahoo Fantasy pipeline for a full season and writes all frames to Unity Catalog Delta tables.

**Source:** `examples/load_yahoo_data_uc.py`

---

## Prerequisites

- A Yahoo Developer application with `client_id`, `client_secret`, and `redirect_uri`.
- A cached OAuth token at `.secrets/yahoo_token.json` (generated on first run).
- Databricks environment with Unity Catalog enabled (`nfl` catalog, `yh` schema pre-created).

---

## 1. Install Dependencies

```python
%pip install polars requests-oauthlib
```

---

## 2. Setup & Imports

```python
import json
import os
from pathlib import Path
import sys

import polars as pl

from nfl.common.utils import find_project_root

project_root = find_project_root()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.yahoo_fantasy.pipeline import PipelineConfig, PipelineDiagnosticsConfig, run_pipeline
from nfl.yahoo_fantasy.storage.unity_catalog import YahooUCTableConfig
from nfl.yahoo_fantasy.auth import build_oauth_session, load_token
```

---

## 3. Configure Run Controls

```python
# --- Required Inputs ---
LEAGUE_KEY = "461.l.717896"
SPORT = "nfl"

# --- Season & Week Range ---
TARGET_SEASON = 2024
START_WEEK = 1
END_WEEK = 17
USE_CACHE = False
INCLUDE_UNROSTERED_PLAYER_STATS = True

# --- Unity Catalog Target ---
CATALOG = "nfl"
SCHEMA = "yh"
WRITE_MODE = "overwrite"   # overwrite | append | merge
UC_DRY_RUN = False
```

---

## 4. Authenticate

The pipeline loads credentials from a local `.secrets/` directory. On first run, complete the Yahoo OAuth browser flow and save the token; subsequent runs use the cached token automatically.

```python
credentials_path = project_root / ".secrets" / "credentials.json"
token_path = project_root / ".secrets" / "yahoo_token.json"

with open(credentials_path) as f:
    creds = json.load(f)

oauth_session = build_oauth_session(
    client_id=creds["client_id"],
    client_secret=creds["client_secret"],
    redirect_uri=creds["redirect_uri"],
    token_path=token_path,
    auth_code=None,
    open_browser=False,
)

print("OAuth session ready")
```

---

## 5. Run the Pipeline

```python
uc_table_config = YahooUCTableConfig(
    catalog=CATALOG,
    nfl_schema=SCHEMA,
    nba_schema=f"{SCHEMA}_nba",
    common_schema=SCHEMA,
    write_mode=WRITE_MODE,
)

full_cfg = PipelineConfig(
    storage_target="unity_catalog",
    use_cache=USE_CACHE,
    validate_contracts=True,
    require_nfl_player_points=False,
    include_nfl_unrostered_player_stats=INCLUDE_UNROSTERED_PLAYER_STATS,
    start_week=START_WEEK,
    end_week=END_WEEK,
    uc_table_config=uc_table_config,
    uc_dry_run=UC_DRY_RUN,
    diagnostics=PipelineDiagnosticsConfig(
        enabled=True,
        emit_stage_progress=True,
        capture_frame_summaries=True,
        capture_request_stats=True,
    ),
)

result = run_pipeline(
    league_key=LEAGUE_KEY,
    sport=SPORT,
    oauth_session=oauth_session,
    config=full_cfg,
)

print("Pipeline completed")
print(f"  Frames: {sorted(result.frames.keys())}")
```

---

## 6. Persist to Unity Catalog

```python
from nfl.yahoo_fantasy.storage.unity_catalog import persist_yahoo_to_uc_tables

uc_results = persist_yahoo_to_uc_tables(
    frames=result.frames,
    config=uc_table_config,
    dry_run=UC_DRY_RUN,
)

for wr in uc_results:
    print(f"  {wr.target}: {wr.written_rows} rows ({wr.mode})")
```

---

## 7. Validate

```python
# Quick read-back validation
df = spark.table(f"{CATALOG}.{SCHEMA}.player_stats_weekly")
print(f"player_stats_weekly row count: {df.count()}")
df.show(5, truncate=False)
```

---

## Output Tables

After a successful run, the following tables are available in `nfl.yh`:

| Table | Description |
|---|---|
| `league` | League metadata |
| `team` | Team information |
| `player` | Player dimension (all seasons) |
| `player_deduped` | One row per player ID (latest season) |
| `player_stats_weekly` | Weekly fantasy points per player |
| `roster_entries` | Weekly roster snapshots |
| `matchups` | Head-to-head matchup results |
| `draft_pick` | Draft picks with auction prices |
| `standings` | Season standings |
| `transactions` | Waiver/trade transactions |

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `TokenExpiredError` | Cached OAuth token has expired | Delete token file and re-authenticate |
| `AssertionError: CATALOG must be set` | `CATALOG` or `SCHEMA` variable is empty | Set both variables before running |
| `uc_dry_run=True` → no rows written | Dry-run mode is on | Set `UC_DRY_RUN = False` when ready to write |
| Missing weeks in `player_stats_weekly` | `end_week` is set too low | Increase `END_WEEK` to match the season length |

---

## See Also

- [Yahoo Fantasy API Reference](../api/yahoo_fantasy.md)
- [Query Unity Catalog Tables](query_tables.md)
- [Match Yahoo ↔ FantasyPros Players](match_yahoo_fantasypros.md)
