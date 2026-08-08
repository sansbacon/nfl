# Example: Load FantasyPros ADP Data

This example ingests FantasyPros Overall ADP rankings for multiple seasons from CSV files stored in a Unity Catalog Volume, combines them, and writes the result to `nfl.fp.fp_adp`.

**Source:** `examples/load_fantasypros_adp_uc.py`

---

## Prerequisites

- FantasyPros ADP CSV files downloaded and uploaded to a Unity Catalog Volume.
  - Expected path pattern: `/Volumes/nfl/default/nfl_volume/FantasyPros_{season}_Overall_ADP_Rankings.csv`
- Databricks environment with Unity Catalog enabled (`nfl` catalog, `fp` schema pre-created).

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
from datetime import date
from pathlib import Path

import polars as pl

from nfl.common.utils import find_project_root

project_root = find_project_root()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.fantasypros_fantasy import FantasyProsApiClient, PipelineConfig, run_pipeline
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig
```

---

## 3. Configure Run Controls

```python
SEASONS = list(range(2020, 2026))

# --- Unity Catalog Target ---
CATALOG = "nfl"
SCHEMA = "fp"
WRITE_MODE = "append"   # overwrite | append | merge
UC_DRY_RUN = False

VOLUME_PATH = "/Volumes/nfl/default/nfl_volume"
```

---

## 4. Parse CSV Files Per Season

The `FantasyProsApiClient.parse_adp_volume_csv()` method handles FantasyPros CSV parsing including:

- `"Player (Bye)"` name/bye-week format extraction
- Team and position parsing
- ADP numeric formatting

```python
from nfl.fantasypros_fantasy.storage.unity_catalog import persist_fp_to_uc_tables

fp_client = FantasyProsApiClient(validate_contracts=False)
all_frames: list[pl.DataFrame] = []

for season in SEASONS:
    csv_path = f"{VOLUME_PATH}/FantasyPros_{season}_Overall_ADP_Rankings.csv"
    data = fp_client.parse_adp_volume_csv(csv_path, season=season)

    adp_df = pl.DataFrame(data.adp_rows)
    player_df = pl.DataFrame(data.players)

    # Join player names for easier querying
    combined = adp_df.join(
        player_df.select(["fp_player_id", "full_name", "position", "team"]),
        on="fp_player_id",
        how="left",
    ).rename({"full_name": "player_name"})

    all_frames.append(combined)
    print(f"  Season {season}: {combined.height} rows")

# Combine all seasons into one DataFrame
final = pl.concat(all_frames, how="diagonal")
print(f"\nTotal combined: {final.height} rows x {final.width} cols")
```

---

## 5. Persist to Unity Catalog

```python
uc_results = persist_fp_to_uc_tables(
    frames={"fp_adp": final},
    config=FantasyProsUCTableConfig(
        catalog=CATALOG,
        schema=SCHEMA,
        write_mode="overwrite",
    ),
    dry_run=UC_DRY_RUN,
)
for wr in uc_results:
    print(f"  {wr.target}: {wr.written_rows} rows")
```

---

## 6. Validate

```python
fq = f"{CATALOG}.{SCHEMA}.fp_adp"
df = spark.table(fq)
print(f"{fq}: {df.count()} total rows")
df.groupBy("season").count().orderBy("season").show()
df.show(5, truncate=False)
```

---

## Output Tables

| Table | Description |
|---|---|
| `fp_adp` | ADP rankings per player per season |

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError` for CSV | Volume path is wrong or file not uploaded | Check the `VOLUME_PATH` and filename pattern |
| Duplicate rows across seasons | Using `WRITE_MODE = "append"` on re-run | Use `"overwrite"` or filter before appending |
| Missing columns in output | CSV format changed between seasons | Check `parse_adp_volume_csv` output schema |

---

## See Also

- [FantasyPros API Reference](../api/fantasypros_fantasy.md)
- [Match Yahoo ↔ FantasyPros Players](match_yahoo_fantasypros.md)
- [Query Unity Catalog Tables](query_tables.md)
