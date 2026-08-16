# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
import numpy as np
import pandas as pd

import pyspark.sql.functions as F
from pyspark.sql import Window


# COMMAND ----------

sdf = spark.table('nfl.sl.vw_current_sl_adp').where(F.col('adp_ppr') < 200)

# COMMAND ----------

display(sdf.select ('full_name', 'position', 'team', 'adp_ppr'))

# COMMAND ----------

# DBTITLE 1,Draft availability model - 14 team snake, pick #1
# 14-team snake draft, position #1
# Odd-round picks only (one per turn, since picks are back-to-back)
NUM_TEAMS = 14
odd_round_picks = {
    '2/3': 29,
    '4/5': 57,
    '6/7': 85,
    '8/9': 113,
    '10/11': 141,
    '12/13': 169,
}

# Add positional ADP rank (required by the trained model)
pos_window = Window.partitionBy('position').orderBy('adp_ppr')
sdf_ranked = sdf.withColumn('pos_adp_rank', F.row_number().over(pos_window))

# Compute availability at all target picks using ff.default.p_available UDF
sdf_ranked.createOrReplaceTempView('sleeper_adp_ranked')

pick_values = ", ".join(f"({p})" for p in odd_round_picks.values())
avail_df = spark.sql(f"""
    SELECT t.full_name, t.position, t.team, t.adp_ppr, t.pos_adp_rank, p.pick,
           ff.default.p_available(t.adp_ppr, t.position, t.pos_adp_rank, p.pick) AS p_avail
    FROM sleeper_adp_ranked t
    CROSS JOIN (VALUES {pick_values}) AS p(pick)
    WHERE t.position NOT IN ('K', 'DEF')
""").toPandas()

# Get Fantasy Life ranks & tiers (PPR, current)
fl_df = spark.table('nfl.fl.fact_fl_ranks') \
    .where((F.col('is_current') == True) & (F.col('scoring_format') == 'PPR')) \
    .select('player', 'position', 'consensus_rank', 'position_tier', 'overall_tier') \
    .toPandas()

# Join on player name + position
avail_df = avail_df.merge(
    fl_df,
    left_on=['full_name', 'position'],
    right_on=['player', 'position'],
    how='left'
).drop(columns=['player'])

# Reverse-map pick number to turn label
pick_to_turn = {v: k for k, v in odd_round_picks.items()}
avail_df['turn'] = avail_df['pick'].map(pick_to_turn)

# For each turn, find players 20-100% likely available
# Max 10 players per position per turn, prioritized by FL consensus rank
targets = avail_df[(avail_df['p_avail'] >= 0.10) & (avail_df['p_avail'] <= 1.00)].copy()
targets = targets.sort_values('consensus_rank', ascending=True, na_position='last')
targets = targets.groupby(['turn', 'position']).head(7)
targets = targets.sort_values(['pick', 'consensus_rank'], ascending=[True, True], na_position='last')

result_df = targets[['turn', 'full_name', 'position', 'team', 'p_avail', 'adp_ppr', 'consensus_rank', 'position_tier', 'overall_tier']].copy()
result_df.columns = ['turn', 'player', 'position', 'team', 'p_available', 'adp_ppr', 'fl_rank', 'pos_tier', 'ovr_tier']
result_df['p_available'] = result_df['p_available'].apply(lambda x: f"{x:.0%}")
display(result_df)

# COMMAND ----------

# MAGIC %md ## Optimization Model

# COMMAND ----------

# DBTITLE 1,Install PuLP
# MAGIC %pip install pulp -q

# COMMAND ----------

# DBTITLE 1,Draft optimizer - minimize tiers
from pulp import *

# --- Build optimization dataset from avail_df (has FL tiers from Cell 4) ---
opt_df = avail_df.dropna(subset=['consensus_rank', 'position_tier', 'overall_tier']).copy()

# Add Round 1 (pick #1) — first overall pick, everyone is available
round1_players = opt_df.drop_duplicates(subset=['full_name', 'position']).copy()
round1_players['pick'] = 1
round1_players['p_avail'] = 1.0
round1_players['turn'] = '1'
opt_df = pd.concat([round1_players, opt_df], ignore_index=True)

# Turns and capacity (1 pick in round 1, 2 per subsequent turn pair)
turns = ['1', '2/3', '4/5', '6/7', '8/9', '10/11', '12/13']
picks_per_turn = {'1': 1, '2/3': 2, '4/5': 2, '6/7': 2, '8/9': 2, '10/11': 2, '12/13': 2}

# Keep only candidates with >= 50% availability
opt_df = opt_df[opt_df['p_avail'] >= 0.50].reset_index(drop=True)
opt_df['idx'] = opt_df.index
wrrb_mask = opt_df['position'].isin(['WR', 'RB'])

# --- Shared constraint builder ---
def build_base_constraints(prob, x, opt_df, turns, picks_per_turn):
    """Add structural + roster constraints common to every solve."""
    for t in turns:
        turn_idxs = opt_df[opt_df['turn'] == t]['idx'].tolist()
        prob += lpSum(x[i] for i in turn_idxs) == picks_per_turn[t]
    for player in opt_df['full_name'].unique():
        player_idxs = opt_df[opt_df['full_name'] == player]['idx'].tolist()
        prob += lpSum(x[i] for i in player_idxs) <= 1
    roster = {'QB': 1, 'TE': 1, 'RB': 5, 'WR': 6}
    for pos, count in roster.items():
        pos_idxs = opt_df[opt_df['position'] == pos]['idx'].tolist()
        prob += lpSum(x[i] for i in pos_idxs) == count

# --- Step 1: Find ideal points for each objective independently ---
# Objective A: minimize overall_tier sum
prob_a = LpProblem("Min_Overall_Tier", LpMinimize)
x_a = LpVariable.dicts("xa", opt_df['idx'].tolist(), cat='Binary')
prob_a += lpSum(opt_df.loc[i, 'overall_tier'] * x_a[i] for i in opt_df['idx'])
build_base_constraints(prob_a, x_a, opt_df, turns, picks_per_turn)
prob_a.solve(PULP_CBC_CMD(msg=0))
min_ovr = int(value(prob_a.objective))

# Objective B: minimize WR+RB position_tier sum
prob_b = LpProblem("Min_Pos_Tier", LpMinimize)
x_b = LpVariable.dicts("xb", opt_df['idx'].tolist(), cat='Binary')
prob_b += lpSum(opt_df.loc[i, 'position_tier'] * x_b[i] for i in opt_df[wrrb_mask]['idx'])
build_base_constraints(prob_b, x_b, opt_df, turns, picks_per_turn)
prob_b.solve(PULP_CBC_CMD(msg=0))
min_pos = int(value(prob_b.objective))

# Get worst-case overall tier when position tier is minimized (upper bound for sweep)
ovr_at_min_pos = int(sum(opt_df.loc[i, 'overall_tier'] for i in opt_df['idx'] if x_b[i].varValue == 1))

print(f"Ideal points:")
print(f"  Min overall tier sum = {min_ovr} (ignoring pos tiers)")
print(f"  Min WR+RB pos tier sum = {min_pos} (overall tier = {ovr_at_min_pos})")
print(f"\nSweeping ε-constraint: overall_tier ∈ [{min_ovr}, {ovr_at_min_pos}]...\n")

# --- Step 2: ε-constraint sweep — minimize pos_tier s.t. overall_tier ≤ ε ---
pareto_rosters = []

for eps in range(min_ovr, ovr_at_min_pos + 1):
    prob_e = LpProblem(f"Pareto_eps_{eps}", LpMinimize)
    x_e = LpVariable.dicts("xe", opt_df['idx'].tolist(), cat='Binary')
    # Primary objective: minimize WR+RB position tier
    prob_e += lpSum(opt_df.loc[i, 'position_tier'] * x_e[i] for i in opt_df[wrrb_mask]['idx'])
    # ε-constraint on overall tier
    prob_e += lpSum(opt_df.loc[i, 'overall_tier'] * x_e[i] for i in opt_df['idx']) <= eps
    build_base_constraints(prob_e, x_e, opt_df, turns, picks_per_turn)
    prob_e.solve(PULP_CBC_CMD(msg=0))

    if prob_e.status == 1:
        pos_val = int(value(prob_e.objective))
        ovr_val = int(sum(opt_df.loc[i, 'overall_tier'] for i in opt_df['idx'] if x_e[i].varValue == 1))
        # Keep only if non-dominated (pos_tier strictly improves vs previous)
        if not pareto_rosters or pos_val < pareto_rosters[-1]['pos_tier_sum']:
            selected_idxs = [i for i in opt_df['idx'] if x_e[i].varValue == 1]
            pareto_rosters.append({
                'ovr_tier_sum': ovr_val,
                'pos_tier_sum': pos_val,
                'players': opt_df[opt_df['idx'].isin(selected_idxs)].sort_values('pick')
            })

print(f"Found {len(pareto_rosters)} Pareto-optimal rosters:\n")
print(f"{'Roster':<8} {'Σ Ovr Tier':<12} {'Σ WR+RB Pos Tier'}")
print("-" * 38)
for i, r in enumerate(pareto_rosters, 1):
    print(f"  {i:<6} {r['ovr_tier_sum']:<12} {r['pos_tier_sum']}")

# Display each Pareto roster
for i, r in enumerate(pareto_rosters, 1):
    print(f"\n{'='*60}")
    print(f"Roster {i}: Overall Tier Sum = {r['ovr_tier_sum']}  |  WR+RB Pos Tier Sum = {r['pos_tier_sum']}")
    print(f"{'='*60}")
    out = r['players'][['turn', 'full_name', 'position', 'team', 'p_avail',
                        'adp_ppr', 'consensus_rank', 'position_tier', 'overall_tier']].copy()
    out.columns = ['turn', 'player', 'pos', 'team', 'p_avail',
                   'adp', 'fl_rank', 'pos_tier', 'ovr_tier']
    out['p_avail'] = out['p_avail'].apply(lambda v: f"{v:.0%}")
    display(out)

# COMMAND ----------

