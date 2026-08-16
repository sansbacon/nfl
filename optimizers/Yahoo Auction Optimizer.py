# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md ## Yahoo Draft Optimizer

# COMMAND ----------

# MAGIC %md ## Setup

# COMMAND ----------

from scipy.optimize import milp, LinearConstraint, Bounds
import numpy as np
import pandas as pd
import pyspark.sql.functions as F

# COMMAND ----------

dbutils.widgets.text('BUDGET', str(200 - 1))
dbutils.widgets.text('STARTER_BUDGET_PCT', '.85')

# COMMAND ----------

BUDGET = int(dbutils.widgets.get('BUDGET'))
STARTER_BUDGET_PCT = float(dbutils.widgets.get('STARTER_BUDGET_PCT'))

# COMMAND ----------

proj = (
  spark.table('nfl.default.auction_price_projections')
  .select(F.col('player_id').alias('yahoo_id'), 'position', 'low', 'median', 'high')
  .toPandas()
  .set_index('yahoo_id')
)

# COMMAND ----------

sql = """
  SELECT 
    r.player, 
    r.consensus_rank,
    r.overall_tier,
    r.position_tier,
    xw.yahoo_id
  FROM nfl.fl.fact_fl_ranks r
  JOIN nfl.fl.fl_player_map m ON r.player = m.display_name
  JOIN nfl.common.dim_ff_player_ids xw ON m.mfl_id = xw.mfl_id
  WHERE r.is_current = true
"""

# COMMAND ----------

# need to join sdf and ranks
ranks = (
  spark.sql(sql)
  .toPandas()
  .set_index('yahoo_id')
  .join(proj, how='left')
)

# COMMAND ----------

players = 13

positions = {
    'QB': (1, 1),
    'TE': (1, 1),
    'RB': (5, 5),
    'WR': (6, 6),
}

start = {
    'QB': (1, 1),
    'TE': (1, 2),
    'RB': (2, 3),
    'WR': (3, 4),
}

# COMMAND ----------

# MAGIC %md ## Optimizer

# COMMAND ----------

# Starters per position (flex = WR)
starter_counts = {'QB': 1, 'RB': 2, 'WR': 4, 'TE': 1}
total_starters = sum(starter_counts.values())

# COMMAND ----------

# Build optimizer input from ranks (already has tiers + price projections)
pdf = ranks.reset_index().copy()

# Drop players missing projection data (not in auction projections table)
pdf = pdf.dropna(subset=['median'])

# Conservative cost: sample from a distribution skewed toward high end
# Mean = midpoint of median..high, std derived from the full low..high spread
# Players <$3 median are floor-priced → always $1
rng = np.random.default_rng()
mean = (pdf['median'] + pdf['high']) / 2
std = (pdf['high'] - pdf['low']) / 4  # ~95% of draws within low..high
sampled = np.clip(rng.normal(loc=mean, scale=std), pdf['low'].values, (pdf['high'] + 2).values)
pdf['conservative_cost'] = np.where(pdf['median'] >= 3, np.ceil(sampled).astype(int), pdf['median'])

# Derive position_rank from consensus_rank within each position
pdf['position_rank'] = pdf.groupby('position')['consensus_rank'].rank(method='dense').astype(int)

# Unranked players get worst-case tier so optimizer deprioritizes them
pdf['overall_tier'] = pdf['overall_tier'].fillna(pdf['overall_tier'].max() + 1)
pdf['position_tier'] = pdf['position_tier'].fillna(pdf['position_tier'].max() + 1)

pdf = pdf.sort_values(['position', 'position_rank']).reset_index(drop=True)
n = len(pdf)
costs = pdf['conservative_cost'].values.astype(float)

# --- ILP with starter designation ---
# Variables: x[0..n-1] = roster selection, s[n..2n-1] = starter designation
# Total variables = 2n

# COMMAND ----------

# Multi-objective (lexicographic):
#   1. Primary: minimize sum(overall_tier) for full roster
#   2. Secondary: minimize sum(position_tier) for WR/TE, constrained to
#      primary objective within 1 tier of optimal

wr_te_mask = pdf['position'].isin(['WR', 'TE']).astype(float).values
overall_tiers = pdf['overall_tier'].values.astype(float)
position_tiers = pdf['position_tier'].values.astype(float)

# --- Primary objective: minimize overall_tier ---
c_primary = np.zeros(2 * n)
c_primary[:n] = overall_tiers

bounds = Bounds(lb=0, ub=1)
integrality = np.ones(2 * n)

A_ub_rows = []
b_ub_rows = []
A_eq_rows = []
b_eq_rows = []

# 1. Exactly `players` on roster
row = np.zeros(2 * n)
row[:n] = 1
A_eq_rows.append(row)
b_eq_rows.append(players)

# 2. Budget constraint: sum of roster costs <= BUDGET
row = np.zeros(2 * n)
row[:n] = costs
A_ub_rows.append(row)
b_ub_rows.append(BUDGET)

# 3. Roster position constraints (min/max from `positions`)
for pos, (pos_min, pos_max) in positions.items():
    mask = (pdf['position'] == pos).astype(float).values
    # min: -sum(x) <= -pos_min
    row = np.zeros(2 * n)
    row[:n] = -mask
    A_ub_rows.append(row)
    b_ub_rows.append(-pos_min)
    # max: sum(x) <= pos_max
    row = np.zeros(2 * n)
    row[:n] = mask
    A_ub_rows.append(row)
    b_ub_rows.append(pos_max)

# 4. Linking: s[i] <= x[i] → s[i] - x[i] <= 0
for i in range(n):
    row = np.zeros(2 * n)
    row[n + i] = 1   # s[i]
    row[i] = -1      # -x[i]
    A_ub_rows.append(row)
    b_ub_rows.append(0)

# 5. Starter position counts (exact): sum(s) per position = starter_counts
for pos, count in starter_counts.items():
    mask = (pdf['position'] == pos).astype(float).values
    row = np.zeros(2 * n)
    row[n:] = mask
    A_eq_rows.append(row)
    b_eq_rows.append(count)

# 6. Starter budget >= 80%: -sum(s[i] * cost[i]) <= -0.80 * BUDGET
row = np.zeros(2 * n)
row[n:] = -costs
A_ub_rows.append(row)
b_ub_rows.append(-STARTER_BUDGET_PCT * BUDGET)

# 7. At least 1 RB in top 4 position tiers
rb_top4 = ((pdf['position'] == 'RB') & (pdf['position_tier'] <= 4)).astype(float).values
row = np.zeros(2 * n)
row[:n] = -rb_top4
A_ub_rows.append(row)
b_ub_rows.append(-1)

# 8. At least 2 RBs in top 6 position tiers
rb_top6 = ((pdf['position'] == 'RB') & (pdf['position_tier'] <= 6)).astype(float).values
row = np.zeros(2 * n)
row[:n] = -rb_top6
A_ub_rows.append(row)
b_ub_rows.append(-2)

constraints = [
    LinearConstraint(np.array(A_eq_rows), np.array(b_eq_rows), np.array(b_eq_rows)),
    LinearConstraint(np.array(A_ub_rows), -np.inf, np.array(b_ub_rows)),
]

result_primary = milp(c_primary, integrality=integrality, bounds=bounds, constraints=constraints)
assert result_primary.success, f'ERROR: Primary objective failed — {result_primary.message}'

optimal_overall = result_primary.fun
print(f"Primary solve: min overall_tier sum = {optimal_overall:.0f}")

# --- Secondary objective: minimize position_tier for WR/TE ---
# Constrain overall_tier to within 1 tier of primary optimum
c_secondary = np.zeros(2 * n)
c_secondary[:n] = wr_te_mask * position_tiers

# Add constraint: sum(overall_tier * x) <= optimal + 1 tier slack
overall_cap_row = np.zeros(2 * n)
overall_cap_row[:n] = overall_tiers
A_ub_secondary = np.vstack([np.array(A_ub_rows), overall_cap_row])
b_ub_secondary = np.append(np.array(b_ub_rows), optimal_overall + 1)

constraints_secondary = [
    LinearConstraint(np.array(A_eq_rows), np.array(b_eq_rows), np.array(b_eq_rows)),
    LinearConstraint(A_ub_secondary, -np.inf, b_ub_secondary),
]

result = milp(c_secondary, integrality=integrality, bounds=bounds, constraints=constraints_secondary)
assert result.success, f'ERROR: Secondary objective failed — {result.message}'

# Report both objectives
final_x = result.x[:n].round().astype(int)
final_overall = (final_x * overall_tiers).sum()
final_pos_tier = (final_x * wr_te_mask * position_tiers).sum()
print(f"Secondary solve: overall_tier sum = {final_overall:.0f} (cap: {optimal_overall + 1:.0f}), WR/TE position_tier sum = {final_pos_tier:.0f}")

# COMMAND ----------

# Extract roster and starter designations
x_vals = result.x[:n].round().astype(int).astype(bool)
s_vals = result.x[n:].round().astype(int).astype(bool)

roster = pdf.loc[x_vals, ['player', 'position', 'position_rank', 'median', 'high', 'conservative_cost']].copy()
roster['starter'] = s_vals[x_vals]
roster = roster.sort_values(['position', 'position_rank']).reset_index(drop=True)

total_cost = roster['conservative_cost'].sum()
starter_cost = roster.loc[roster['starter'], 'conservative_cost'].sum()
bench_cost = total_cost - starter_cost

print(f"Optimal Conservative Roster ({players} players, ${BUDGET} budget)")
print(f"Starter budget: ${starter_cost:.0f} ({starter_cost/BUDGET:.0%}) | Bench: ${bench_cost:.0f} ({bench_cost/BUDGET:.0%})")
print(f"Constraint: ≥{STARTER_BUDGET_PCT:.0%} on starters ({total_starters} starters, flex=WR)")
print(f"{'='*70}")
for pos in ['QB', 'RB', 'WR', 'TE']:
    pos_players = roster[roster['position'] == pos]
    starters = pos_players[pos_players['starter']]
    bench = pos_players[~pos_players['starter']]
    print(f"\n  {pos} ({len(starters)} start, {len(bench)} bench):")
    for _, row in starters.iterrows():
        print(f"    ★ {row['player']:<22} Rank {row['position_rank']:<3} "
              f"Med ${row['median']:<3} High ${row['high']:<3} → ${row['conservative_cost']:.0f}")
    for _, row in bench.iterrows():
        print(f"      {row['player']:<22} Rank {row['position_rank']:<3} "
              f"Med ${row['median']:<3} High ${row['high']:<3} → ${row['conservative_cost']:.0f}")

print(f"\n{'='*70}")
print(f"Total: ${total_cost:.0f} / ${BUDGET}  |  Remaining: ${BUDGET - total_cost:.0f}")

# COMMAND ----------

