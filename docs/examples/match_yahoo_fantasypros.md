# Example: Match Yahoo ↔ FantasyPros Players

This example builds a player crosswalk between Yahoo Fantasy and FantasyPros by reading the Yahoo player table from Unity Catalog, running the FantasyPros matching pipeline, and writing the crosswalk back to `nfl.fp`.

**Source:** `examples/match_yahoo_fantasypros_uc.py`

**Prerequisite:** Run the [Load Yahoo Data](load_yahoo_data.md) example first to populate `nfl.yh.player_deduped`.

---

## Prerequisites

- `nfl.yh.player_deduped` table exists (from the Yahoo pipeline).
- `nfl.fp.fp_adp` table exists (from the FantasyPros ADP pipeline). This is the multi-season ADP table; the `nfl_fp_current_adp` materialized snapshot is not required for this example.
- Databricks environment with Unity Catalog enabled.

---

## 1. Install Dependencies

```python
%pip install polars lxml
dbutils.library.restartPython()
```

---

## 2. Setup & Imports

```python
import sys
from pathlib import Path

import polars as pl

from nfl.common.utils import find_project_root

project_root = find_project_root()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.fantasypros_fantasy import PipelineConfig, fp_adp_records_to_fp_players, run_pipeline
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig
from nfl.storage_uc import UCTableConfig, persist_to_uc_tables
```

---

## 3. Configure Run Controls

```python
SEASON = 2025

CATALOG = "nfl"
YAHOO_SCHEMA = "yh"
FP_SCHEMA = "fp"
WRITE_MODE = "overwrite"
UC_DRY_RUN = False

# Backfill prior seasons to catch players no longer active
BACKFILL_SEASONS = [2021, 2022, 2023, 2024]
```

---

## 4. Load Yahoo Players from Unity Catalog

```python
yahoo_player_spark = spark.table(f"{CATALOG}.{YAHOO_SCHEMA}.player_deduped")
yahoo_players = yahoo_player_spark.toPandas().to_dict(orient="records")

print(f"Yahoo players loaded (deduped): {len(yahoo_players)}")
```

---

## 5. Load FantasyPros ADP Players from Unity Catalog

```python
fp_adp_spark = spark.table(f"{CATALOG}.{FP_SCHEMA}.fp_adp")
fp_adp_records = fp_adp_spark.filter(f"season = {SEASON}").toPandas().to_dict(orient="records")

print(f"FP ADP players (season={SEASON}): {len(fp_adp_records)}")

# Convert ADP records to fp_player format for the crosswalk builder
fp_players = fp_adp_records_to_fp_players(fp_adp_records)
```

---

## 6. Build the Crosswalk

The matching pipeline uses name normalization and fuzzy matching to link FantasyPros player IDs to Yahoo player IDs.

```python
from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk

crosswalk_records = build_fp_yahoo_crosswalk(
    fp_players=fp_players,
    yahoo_players=yahoo_players,
)
crosswalk_df = pl.DataFrame(crosswalk_records) if crosswalk_records else pl.DataFrame()

print(f"Crosswalk matches: {crosswalk_df.height}")

if crosswalk_df.height > 0 and "match_method" in crosswalk_df.columns:
    print("\nMatch method breakdown:")
    print(crosswalk_df.group_by("match_method").agg(pl.len()))
```

---

## 7. Persist Crosswalk to Unity Catalog

```python
uc_results = persist_to_uc_tables(
    frames={"nfl_fp_yahoo_player_map": crosswalk_df},
    config=UCTableConfig(
        catalog=CATALOG,
        schema=FP_SCHEMA,
        write_mode=WRITE_MODE,
    ),
    dry_run=UC_DRY_RUN,
)
for wr in uc_results:
    print(f"  {wr.target}: {wr.written_rows} rows ({wr.mode})")
```

---

## 8. Validate

```python
fq_crosswalk = f"{CATALOG}.{FP_SCHEMA}.nfl_fp_yahoo_player_map"
count = spark.table(fq_crosswalk).count()
print(f"{fq_crosswalk}: {count} rows")
spark.table(fq_crosswalk).show(10, truncate=False)
```

---

## Understanding Match Methods

| Match Method | Description |
|---|---|
| `exact` | Names match exactly after normalization |
| `fuzzy` | Names match above the configured fuzzy threshold |
| `manual` | Match was applied via a manual override |

Review the crosswalk to identify players with no match — these may need manual overrides or indicate data quality issues in one of the source tables.

---

## Output Tables

| Table | Schema | Description |
|---|---|---|
| `nfl_fp_yahoo_player_map` | `nfl.fp` | Yahoo↔FantasyPros player crosswalk |

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| Low match count | Season mismatch between Yahoo and FP tables | Check that both tables cover the same season |
| Many `fuzzy` matches | Name formatting differences across sources | Lower the fuzzy threshold or add manual overrides |
| Crosswalk table missing | Previous step failed silently | Check `uc_dry_run` flag and re-run |

---

## See Also

- [FantasyPros API Reference](../api/fantasypros_fantasy.md)
- [Entity Standardization API Reference](../api/entity_standardization.md)
- [Load Yahoo Data](load_yahoo_data.md)
- [Load FantasyPros ADP](load_fantasypros_adp.md)
- [Query Unity Catalog Tables](query_tables.md)
