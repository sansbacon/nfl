# Databricks notebook source
# DBTITLE 1,Bestball Roster Composition
# MAGIC %md
# MAGIC ## Bestball Roster Composition
# MAGIC
# MAGIC Analyzes optimal roster composition for best-ball formats using historical player scoring data.
# MAGIC Simulates positional allocation strategies (e.g., 2 QB vs 3 QB builds, RB-heavy vs WR-heavy).
# MAGIC
# MAGIC > **Note:** Migrated from `ffdatwarehouse/research/`. Originally run 2020-2021.
# MAGIC > Uses deprecated `/dbfs/FileStore/` paths and legacy MFL API. Needs updating to use
# MAGIC > `nfl.nflverse_fantasy` or UC tables for modern execution.

# COMMAND ----------

# DBTITLE 1,Imports
from functools import partial
from itertools import combinations

import numpy as np
import pandas as pd
import requests

# COMMAND ----------

# DBTITLE 1,Helper functions
def remap(df, col, mapping):
    """Remaps column, uses existing value as default"""
    return df.loc[:, col].map(mapping).fillna(df[col])


def add_per_game(df, statcol='fantasy_pts', countcol='week', groupcols=None, aggcolname='ppg'):
    """Adds per game stats to dataframe"""
    if not groupcols:
        groupcols = ['season', 'position', 'player_id']
    tmp = (
      df.groupby(groupcols)
      .agg({statcol: 'mean', countcol: 'count'})
      .reset_index()
      .rename(columns={statcol: aggcolname, countcol: 'gp'})
    )
    tmp[f'posrk_{aggcolname}_year'] = (
     tmp.groupby(groupcols[0:2])[aggcolname].rank(method='first', ascending=False)
    )
    return df.join(tmp.set_index(groupcols), how='left', on=groupcols)


def combo_diff(dfs, n, shuffle_weeks=False, iterations=0):
    """Calculates scoring differences for two groups"""
    if len(dfs) != len(n):
        raise ValueError(f'length of dfs and n must be the same: {len(dfs)} != {len(n)}')
    if not shuffle_weeks:
        for combo in combinations(range(len(dfs)), r=2):
            t1 = dfs[combo[0]]
            t2 = dfs[combo[1]]
            week_diffs = [week_diff(t1, t2, week, n) for week in range(1, 17)]
            return np.sum(week_diffs), week_diffs
    else:
        shuffle_diffs = []
        for combo in combinations(range(len(dfs)), r=2):
            t1 = dfs[combo[0]]
            t2 = dfs[combo[1]]
            for i in range(iterations):
                t1.loc[:, 'week'] = t1.groupby('player_id')['week'].transform(np.random.permutation)
                t2.loc[:, 'week'] = t2.groupby('player_id')['week'].transform(np.random.permutation)
                shuffle_diffs.append(np.sum([week_diff(t1, t2, week, n) for week in range(1, 17)]))
        return np.mean(shuffle_diffs), shuffle_diffs


def week_diff(df1, df2, week, n):
    """Calculates week difference"""
    v1 = weekly_scoring(df1.loc[df1.week == week, 'fantasy_pts'], n=n[0])
    v2 = weekly_scoring(df2.loc[df2.week == week, 'fantasy_pts'], n=n[1])
    return v2 - v1


def weekly_scoring(scores, n):
    """Calculates weekly scoring for n players"""
    return round(np.sum(np.sort(scores)[::-1][0:n]), 2)

# COMMAND ----------

# DBTITLE 1,Load data (LEGACY - needs update)
# TODO: Update to use nfl.nflverse_fantasy or UC tables
# Original path: /dbfs/FileStore/combined.csv
# df = add_per_game(pd.read_csv('/dbfs/FileStore/combined.csv'))
raise NotImplementedError('Update data source path — /dbfs/FileStore/ is deprecated')

# COMMAND ----------

# DBTITLE 1,Analysis: positional value comparisons
# Example: value of top 2 QBs vs 3-5 range
# diffs = []
# for _ in range(500):
#     df1 = df.query('position == "QB" & season == 2019 & posrk_year < 3').copy()
#     df2 = df.query('position == "QB" & season == 2019 & posrk_year > 2 & posrk_year < 6').copy()
#     n = (1, 1)
#     tot, vals = combo_diff([df1, df2], n, shuffle_weeks=True, iterations=3)
#     diffs.append(tot)