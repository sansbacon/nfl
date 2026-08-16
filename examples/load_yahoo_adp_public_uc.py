# Databricks notebook source
# DBTITLE 1,Load Yahoo ADP + Salary Cap (Public, No OAuth)
# MAGIC %md
# MAGIC # Load Yahoo ADP + Salary Cap → Unity Catalog (Public Endpoint, No OAuth)
# MAGIC
# MAGIC **Workaround for the broken Yahoo Developer OAuth app** (persistent 403 `"This application is not authorized to perform this action"` on the official Fantasy Sports API, confirmed at the app-verification level even with a freshly re-consented token and Fantasy Sports Read enabled).
# MAGIC
# MAGIC The public Draft Analysis page (`https://football.fantasysports.yahoo.com/f1/draftanalysis`) renders its table client-side by calling Yahoo's **public read-only** API host directly — `pub-api-ro.fantasysports.yahoo.com` — using a `{gameId}.l.public` pseudo-league. This host requires **no OAuth token and no app authorization**; it's the same backend the logged-out webpage itself uses.
# MAGIC
# MAGIC A single request with `count=2000` returns the **entire** player pool for a season (no pagination needed) with both:
# MAGIC - `draft_analysis.average_pick` / `average_round` / `percent_drafted` → ADP
# MAGIC - `draft_analysis.average_cost` → Salary Cap (auction $ value)
# MAGIC - `preseason_*` variants of each
# MAGIC
# MAGIC Writes into the existing `nfl.yh.fact_yahoo_adp` table (PK: `player_key`, `game_id`, `snapshot_date`), the same target used by prior Yahoo ADP loads.
# MAGIC
# MAGIC **Note:** `game_id` differs per NFL season (e.g. 470 = 2026). If unknown, increment from the prior season's `game_id` (Yahoo NFL game ids increase by ~9-11 each year) or check the page source of `draftanalysis` for `var gameId`.

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'nfl')
dbutils.widgets.text('SCHEMA', 'yh')
dbutils.widgets.text('GAME_ID', '470')
from datetime import date
dbutils.widgets.text('SNAPSHOT_DATE', date.today().isoformat())

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
CATALOG = dbutils.widgets.get('CATALOG')
SCHEMA = dbutils.widgets.get('SCHEMA')
GAME_ID = int(dbutils.widgets.get('GAME_ID'))
SNAPSHOT_DATE = dbutils.widgets.get('SNAPSHOT_DATE')

assert all((CATALOG, SCHEMA, GAME_ID, SNAPSHOT_DATE)), (
    f'ERROR: {CATALOG=} {SCHEMA=} {GAME_ID=} {SNAPSHOT_DATE=} must be set'
)

print(f"Target: {CATALOG}.{SCHEMA}.fact_yahoo_adp")
print(f"game_id={GAME_ID} (season inferred from Yahoo), snapshot_date={SNAPSHOT_DATE}")

# COMMAND ----------

# DBTITLE 1,Fetch Public Draft Analysis (No OAuth)
import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def fetch_public_draft_analysis(game_id: int, count: int = 2000, sort_key: str = "average_pick") -> list[dict]:
    """Fetch the full public draft-analysis player pool for a Yahoo game_id.

    Hits pub-api-ro.fantasysports.yahoo.com directly (no OAuth) using the
    {game_id}.l.public pseudo-league — the same backend the logged-out
    draftanalysis webpage calls client-side. A single request with a large
    `count` returns the entire pool (no pagination required).
    """
    path = (
        f"league/{game_id}.l.public;out=settings/players;position=ALL;start=0;count={count};"
        f"sort={sort_key};search=;out=auction_values,ranks;ranks=o-rank;out=expert_ranks;"
        f"expert_ranks.rank_type=projected_season_remaining/draft_analysis;cut_types=diamond;slices=last7days"
    )
    url = f"https://pub-api-ro.fantasysports.yahoo.com/fantasy/v2/{path}?format=json_f"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return payload["fantasy_content"]["league"]["players"]


def flatten_player(entry: dict) -> dict:
    player = entry["player"]
    da = player.get("draft_analysis") or {}
    return {
        "player_key": player.get("player_key"),
        "player_id": player.get("player_id"),
        "full_name": (player.get("name") or {}).get("full"),
        "display_position": player.get("display_position"),
        "editorial_team_abbr": player.get("editorial_team_abbr"),
        "average_pick": da.get("average_pick"),
        "average_round": da.get("average_round"),
        "average_cost": da.get("average_cost"),
        "percent_drafted": da.get("percent_drafted"),
        "preseason_average_pick": da.get("preseason_average_pick"),
        "preseason_average_round": da.get("preseason_average_round"),
        "preseason_average_cost": da.get("preseason_average_cost"),
        "preseason_percent_drafted": da.get("preseason_percent_drafted"),
    }


players_raw = fetch_public_draft_analysis(GAME_ID)
rows = [flatten_player(p) for p in players_raw]
print(f"Fetched {len(rows)} players for game_id={GAME_ID}")
print(f"  with average_pick: {sum(1 for r in rows if r['average_pick'] not in (None, '-'))}")
print(f"  with average_cost: {sum(1 for r in rows if r['average_cost'] not in (None, '-'))}")

# COMMAND ----------

# DBTITLE 1,Merge into fact_yahoo_adp
from pyspark.sql import functions as F
from delta.tables import DeltaTable


def clean_numeric(colname: str, target_type: str):
    return F.expr(f"try_cast(nullif({colname}, '-') as {target_type})")


df = spark.createDataFrame(rows)
df = (
    df.withColumn("game_id", F.lit(GAME_ID).cast("int"))
    .withColumn("snapshot_date", F.lit(SNAPSHOT_DATE).cast("date"))
    .withColumn("average_pick", clean_numeric("average_pick", "decimal(6,2)"))
    .withColumn("average_round", clean_numeric("average_round", "decimal(4,2)"))
    .withColumn("average_cost", clean_numeric("average_cost", "decimal(6,2)"))
    .withColumn("percent_drafted", clean_numeric("percent_drafted", "decimal(5,2)"))
    .select("player_key", "game_id", "snapshot_date", "average_pick", "average_round", "average_cost", "percent_drafted")
)

target_fq = f"{CATALOG}.{SCHEMA}.fact_yahoo_adp"
target_table = DeltaTable.forName(spark, target_fq)
(
    target_table.alias("t")
    .merge(
        df.alias("s"),
        "t.player_key = s.player_key AND t.game_id = s.game_id AND t.snapshot_date = s.snapshot_date",
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

print(f"Merged {df.count()} rows into {target_fq} for game_id={GAME_ID}, snapshot_date={SNAPSHOT_DATE}")

# COMMAND ----------

# DBTITLE 1,Verify
spark.sql(f"""
    SELECT game_id, snapshot_date, count(*) AS rows,
           count(average_cost) AS with_cost, count(average_pick) AS with_adp
    FROM {CATALOG}.{SCHEMA}.fact_yahoo_adp
    WHERE game_id = {GAME_ID}
    GROUP BY game_id, snapshot_date
    ORDER BY snapshot_date
""").show()

dbutils.notebook.exit(f'Success - Yahoo public ADP/salary cap load complete for game_id={GAME_ID}, snapshot_date={SNAPSHOT_DATE}')