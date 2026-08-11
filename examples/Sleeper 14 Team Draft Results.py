# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md ## Sleeper 14-team ADP

# COMMAND ----------

import requests
import pandas as pd

# COMMAND ----------

# DBTITLE 1,Configuration
SEASON = 2026
NUM_TEAMS = 14
WINDOW_DAYS = 7
SCORING = "adp_ppr"  # options: adp_std, adp_ppr, adp_half_ppr, adp_2qb, adp_dynasty
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]

# COMMAND ----------

# DBTITLE 1,Fetch 14-team ADP from Sleeper API
# Sleeper projections endpoint (no auth required)
# The `teams` param filters to N-team leagues; `window` filters to last N days
position_params = "&".join(f"position[]={p}" for p in POSITIONS)
adp_url = (
    f"https://api.sleeper.com/projections/nfl/{SEASON}"
    f"?season_type=regular&{position_params}"
    f"&order_by={SCORING}&teams={NUM_TEAMS}&window={WINDOW_DAYS}"
)

print(f"Requesting: {adp_url}")
resp = requests.get(adp_url, timeout=30)
resp.raise_for_status()
adp_data = resp.json()

# If teams filter returns no data (e.g. early in season), fall back to full pool
if not adp_data:
    print(f"⚠️  No {NUM_TEAMS}-team draft data in the last {WINDOW_DAYS} days (season just started).")
    print("   Falling back to full draft pool (all team sizes)...")
    fallback_url = (
        f"https://api.sleeper.com/projections/nfl/{SEASON}"
        f"?season_type=regular&{position_params}"
        f"&order_by={SCORING}&window={WINDOW_DAYS}"
    )
    resp = requests.get(fallback_url, timeout=30)
    resp.raise_for_status()
    adp_data = resp.json()

print(f"\nRetrieved ADP data for {len(adp_data)} players")
print(f"Season: {SEASON} | Teams: {NUM_TEAMS} | Window: {WINDOW_DAYS} days | Scoring: PPR")

# COMMAND ----------

# DBTITLE 1,Fetch player metadata from Sleeper
# Fetch all NFL player metadata (keyed by player_id)
players_url = "https://api.sleeper.app/v1/players/nfl"
players_resp = requests.get(players_url, timeout=60)
players_resp.raise_for_status()
players_raw = players_resp.json()

print(f"Fetched metadata for {len(players_raw)} players")

# COMMAND ----------

# DBTITLE 1,Build ADP DataFrame with player details
# Parse projections response (list of {player_id, stats}) joined with player metadata
rows = []
for item in adp_data:
    pid = str(item.get("player_id"))
    stats = item.get("stats") or {}
    adp_val = stats.get(SCORING)
    if adp_val is None or adp_val >= 999:
        continue

    player = players_raw.get(pid, {})
    position = player.get("position")
    if position not in POSITIONS:
        continue

    rows.append({
        "player_id": pid,
        "full_name": player.get("full_name") or f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
        "position": position,
        "team": player.get("team"),
        "adp_ppr": adp_val,
        "adp_half_ppr": stats.get("adp_half_ppr"),
        "adp_std": stats.get("adp_std"),
        "adp_2qb": stats.get("adp_2qb"),
    })

df = pd.DataFrame(rows).sort_values("adp_ppr").reset_index(drop=True)
df.index += 1  # 1-based rank

print(f"{len(df)} players with ADP data (past {WINDOW_DAYS} days)")

# COMMAND ----------

# DBTITLE 1,Display top 200 ADP results
# Show top 200 by PPR ADP
display(
    spark.createDataFrame(
        df[["full_name", "position", "team", "adp_ppr", "adp_half_ppr", "adp_std", "adp_2qb"]]
        .head(200)
    )
)