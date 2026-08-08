# Example: Query Unity Catalog Tables

This example demonstrates how to query NFL fantasy data stored in Unity Catalog Delta tables using both Spark SQL and the Python query API.

**Source:** `examples/query_tables_uc.py`

Tables are stored under:

- `nfl.yh.*` — Yahoo Fantasy league data
- `nfl.fp.*` — FantasyPros ADP and player data

---

## Prerequisites

- Yahoo and FantasyPros pipelines have been run and tables are populated in Unity Catalog.
- Databricks environment with Unity Catalog enabled.

---

## 1. Setup & Imports

```python
import sys
from pathlib import Path

import polars as pl

from nfl.common.utils import find_project_root

project_root = find_project_root()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.yahoo_fantasy.queries import (
    average_scoring_by_position_by_team,
    enrich_weekly_team_points,
    league_average_by_position,
    league_team_info,
    player_points_health,
    standings_summary as query_standings_summary,
    unified_draft_price_analysis,
    weekly_team_points_resolved,
)
from nfl.yahoo_fantasy.presentation import format_table_for_display
from nfl.common.storage import load_uc_table as _load_uc_table

pl.Config.set_tbl_rows(50)
pl.Config.set_fmt_str_lengths(100)
```

---

## 2. Configuration & Helpers

```python
CATALOG = "nfl"
YH_SCHEMA = "yh"
FP_SCHEMA = "fp"

def load_uc_table(schema: str, table: str) -> pl.DataFrame:
    """Load a UC table as a Polars DataFrame."""
    return _load_uc_table(f"{CATALOG}.{schema}.{table}")

def show_table(df: pl.DataFrame, drop_keys: bool = True):
    """Display a table with display formatting."""
    display(format_table_for_display(df, drop_keys=drop_keys))
```

---

## 3. List Available Tables

```python
for schema in [YH_SCHEMA, FP_SCHEMA]:
    tables = [row.tableName for row in spark.sql(f"SHOW TABLES IN {CATALOG}.{schema}").collect()]
    print(f"\n{CATALOG}.{schema}:")
    for t in sorted(tables):
        count = spark.table(f"{CATALOG}.{schema}.{t}").count()
        print(f"  {t}: {count} rows")
```

---

## 4. League & Team Information

```python
league_df = load_uc_table(YH_SCHEMA, "league")
team_df = load_uc_table(YH_SCHEMA, "team")

league_team = league_team_info(league_df=league_df, team_df=team_df)
print("League and Team Information:")
show_table(league_team)
```

---

## 5. Standings

```python
standings_df = load_uc_table(YH_SCHEMA, "standings")

standings = query_standings_summary(standings_df=standings_df, team_df=team_df)
print("Standings:")
show_table(standings)
```

---

## 6. Weekly Scoring Analysis

```python
player_stats_df = load_uc_table(YH_SCHEMA, "player_stats_weekly")
player_df = load_uc_table(YH_SCHEMA, "player")
roster_df = load_uc_table(YH_SCHEMA, "roster_entries")

# Data completeness check
health = player_points_health(player_stats_df)
print("Player Points Health:")
show_table(health)
```

---

## 7. Position Scoring Averages

```python
pos_avg = league_average_by_position(
    player_stats_df=player_stats_df,
    player_df=player_df,
    roster_entries_df=roster_df,
)
print("League Average by Position:")
show_table(pos_avg)
```

---

## 8. Draft Price Analysis (Yahoo + FantasyPros ADP)

Cross-reference Yahoo draft prices against FantasyPros ADP to identify draft-day value and reaches.

```python
draft_df = load_uc_table(YH_SCHEMA, "draft_pick")
fp_adp_df = load_uc_table(FP_SCHEMA, "nfl_fp_current_adp")
fp_crosswalk_df = load_uc_table(FP_SCHEMA, "nfl_fp_yahoo_player_map")

draft_analysis = unified_draft_price_analysis(
    draft_df=draft_df,
    player_df=player_df,
    fp_adp_df=fp_adp_df,
    fp_crosswalk_df=fp_crosswalk_df,
)
print("Draft Price Analysis (Yahoo + FP ADP):")
show_table(draft_analysis)
```

---

## 9. Direct SQL Queries

You can also query Unity Catalog tables directly with Spark SQL:

```sql
-- Top 20 scorers by total fantasy points
SELECT
    p.full_name,
    p.display_position,
    p.editorial_team_abbr AS team,
    SUM(ps.fantasy_points)          AS total_points,
    COUNT(ps.week)                  AS weeks_played,
    ROUND(AVG(ps.fantasy_points), 2) AS avg_ppg
FROM nfl.yh.player_stats_weekly ps
JOIN nfl.yh.player p ON ps.player_key = p.player_key
WHERE ps.fantasy_points > 0
GROUP BY p.full_name, p.display_position, p.editorial_team_abbr
ORDER BY total_points DESC
LIMIT 20
```

```sql
-- ADP value: players drafted significantly cheaper than FP ADP
SELECT
    p.full_name,
    p.display_position,
    d.cost           AS draft_cost,
    fa.adp           AS fp_adp,
    (fa.adp - d.cost) AS value_gap
FROM nfl.yh.draft_pick d
JOIN nfl.yh.player p ON d.player_key = p.player_key
JOIN nfl.fp.nfl_fp_yahoo_player_map cw ON p.player_id = cw.yahoo_player_id
JOIN nfl.fp.nfl_fp_current_adp fa ON cw.fp_player_id = fa.fp_player_id
ORDER BY value_gap DESC
LIMIT 20
```

```sql
-- Weekly scoring by team
SELECT
    t.name             AS team_name,
    ps.week,
    SUM(ps.fantasy_points) AS team_points
FROM nfl.yh.player_stats_weekly ps
JOIN nfl.yh.roster_entries re ON ps.player_key = re.player_key AND ps.week = re.week
JOIN nfl.yh.team t ON re.team_key = t.team_key
GROUP BY t.name, ps.week
ORDER BY t.name, ps.week
```

---

## Available Query Functions

| Function | Description |
|---|---|
| `league_team_info(league_df, team_df)` | Combined league and team metadata |
| `standings_summary(standings_df, team_df)` | Human-readable standings |
| `weekly_team_points_resolved(...)` | Weekly points with team names resolved |
| `build_player_weekly_points(player_stats_df, player_df)` | Player-level weekly scoring |
| `position_weekly_points(player_stats_df, player_df)` | Scoring aggregated by position |
| `team_position_weekly_points(...)` | Scoring by team and position per week |
| `average_scoring_by_position_by_team(...)` | Season averages by team and position |
| `latest_roster_snapshot(roster_entries_df, player_df)` | Most recent roster composition |
| `scoring_quality_by_week(player_stats_df)` | Week-level scoring quality metrics |
| `player_points_health(player_stats_df)` | Data completeness check |
| `league_average_by_position(...)` | League-wide average scoring by position |
| `unified_draft_price_analysis(...)` | Draft value versus FP ADP |

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `Table not found` | Pipeline has not been run yet | Run the Yahoo or FP pipeline first |
| Draft analysis skipped | FP crosswalk or ADP table missing | Run [Load FantasyPros ADP](load_fantasypros_adp.md) and [Match Yahoo ↔ FP](match_yahoo_fantasypros.md) |
| Inconsistent row counts | Cache or partial pipeline run | Re-run the pipeline with `use_cache=False` |

---

## See Also

- [Yahoo Fantasy API Reference](../api/yahoo_fantasy.md)
- [Load Yahoo Data](load_yahoo_data.md)
- [Load FantasyPros ADP](load_fantasypros_adp.md)
