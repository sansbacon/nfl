# Databricks notebook source
# DBTITLE 1,Best Ball - Bye Week Simulation
# MAGIC %md
# MAGIC ## Best Ball - Bye Week Simulation
# MAGIC
# MAGIC Simulates the impact of shared vs. different bye weeks for best-ball roster construction.
# MAGIC Uses nflverse player stats data (2020 season).
# MAGIC
# MAGIC > **Note:** Migrated from `ffdatwarehouse/research/`. Originally run 2021-08-06.

# COMMAND ----------

# DBTITLE 1,Imports
import numpy as np
import pandas as pd

# COMMAND ----------

# DBTITLE 1,Load nflverse player stats
url = 'https://github.com/nflverse/nflfastR-data/raw/master/data/player_stats.parquet'
df = pd.read_parquet(url)

# COMMAND ----------

# DBTITLE 1,Downcast and add scoring
# downcast to float32
cols = df.select_dtypes(include=[np.float64]).columns
df.loc[:, cols] = df.loc[:, cols].astype(np.float32)

# add half-ppr scoring
df = df.assign(fantasy_points_hppr=(df.fantasy_points + df.fantasy_points_ppr) / 2)

# COMMAND ----------

# DBTITLE 1,Add player positions from roster data
# add player positions
pdf = pd.read_csv('https://github.com/nflverse/nflfastR-roster/raw/master/data/nflfastR-roster.csv.gz', compression='gzip', low_memory=False)
df = df.join(pdf.set_index(['gsis_id', 'season']).loc[:, ['full_name', 'position']], how='left', on=['player_id', 'season'])

# COMMAND ----------

# DBTITLE 1,Filter to 2020 season
# filter columns
wanted = ['season', 'week', 'player_id', 'full_name', 'position', 'fantasy_points', 'fantasy_points_ppr', 'fantasy_points_hppr']
df2 = df.loc[df.season == 2020, wanted]

# COMMAND ----------

# DBTITLE 1,Calculate season stats and position ranks
# calculate season stats
seas = (
  df2
  .groupby(['player_id', 'full_name', 'position'], as_index=False)
  .agg(fptot=('fantasy_points', 'sum'),
      fptot_ppr=('fantasy_points_ppr', 'sum'),
      fptot_hppr=('fantasy_points_hppr', 'sum'),
      fppg=('fantasy_points', 'mean'),
      fppg_ppr=('fantasy_points_ppr', 'mean'), 
      fppg_hppr=('fantasy_points_hppr', 'mean')
      )
  .assign(posrk=lambda x: x.groupby('position')['fptot_hppr'].rank(method='first', ascending=False))
)

# COMMAND ----------

# DBTITLE 1,Get top 20 QBs and fill missing weeks
# get the top 20 QBs
qbids = seas.loc[(seas.position == 'QB') & (seas.posrk <= 20), 'player_id']
qbs = df2.loc[df2.player_id.isin(qbids), :]

# we want to be able to simulate a bye
# also need to do it over 16 games based on 15 games from previous year
# so we want to get even-length arrays based on scores from week 1-6
# then we are going to fill with mean value
# then we will test inserting a 0 both at the beginning or one at beginning or one at end
# then we take the greater value of the two
qbs = (
  pd.DataFrame({'season': 2020, 'week': range(1, 17)})
  .merge(qbs.loc[qbs.week < 17, ['player_id']].drop_duplicates(), how='cross')
  .join(qbs.set_index(['season', 'week', 'player_id']), how='left', on=['season', 'week', 'player_id'])
  .assign(full_name=lambda x: x.groupby('player_id')['full_name'].bfill().ffill(),
          position=lambda x: x.groupby('player_id')['position'].bfill().ffill(),
          fantasy_points=lambda x: x.groupby('player_id')['fantasy_points'].transform(lambda y: y.fillna(y.mean())),
          fantasy_points_ppr=lambda x: x.groupby('player_id')['fantasy_points_ppr'].transform(lambda y: y.fillna(y.mean())),
          fantasy_points_hppr=lambda x: x.groupby('player_id')['fantasy_points_hppr'].transform(lambda y: y.fillna(y.mean()))
         )
)

# COMMAND ----------

# DBTITLE 1,Simulation: 2 QBs same vs different bye
# try out vectorized approach
vals = []
iterations = 100
weeks = 16
rng = np.random.default_rng()
shuffled_indices = rng.integers(0, weeks, size=(iterations, weeks)).argsort(axis=1)

for i in range(1000):
    choices = qbids.sample(2).values
    p1 = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[0], 'fantasy_points_hppr'].values[shuffled_indices]))
    p2 = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[1], 'fantasy_points_hppr'].values[shuffled_indices]))
    score = np.array([p1, p2]).max(axis=0)

    p1d = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[0], 'fantasy_points_hppr'].values[shuffled_indices]))
    p2d= np.column_stack((qbs.loc[lambda x: x.player_id == choices[1], 'fantasy_points_hppr'].values[shuffled_indices], np.zeros(iterations)))
    scored = np.array([p1d, p2d]).max(axis=0)
    
    vals.append({'same': score.sum(axis=1).mean(), 'diff': scored.sum(axis=1).mean()})

# COMMAND ----------

# DBTITLE 1,Results: 2 QB bye impact
pd.DataFrame(vals).assign(delta=lambda x: x['diff'] - x.same).describe()

# COMMAND ----------

# DBTITLE 1,Simulation: 3 QBs bye configurations
# 3 QBs, 2 with same bye
vals = []
iterations = 100
weeks = 16
rng = np.random.default_rng()
shuffled_indices = rng.integers(0, weeks, size=(iterations, weeks)).argsort(axis=1)

for i in range(1000):
    # all same bye
    choices = qbids.sample(3).values
    p1 = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[0], 'fantasy_points_hppr'].values[shuffled_indices]))
    p2 = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[1], 'fantasy_points_hppr'].values[shuffled_indices]))
    p3 = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[2], 'fantasy_points_hppr'].values[shuffled_indices]))
    score = np.array([p1, p2, p3]).max(axis=0)

    # two share same bye
    p1d = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[0], 'fantasy_points_hppr'].values[shuffled_indices]))
    p2d= np.column_stack((qbs.loc[lambda x: x.player_id == choices[1], 'fantasy_points_hppr'].values[shuffled_indices], np.zeros(iterations)))
    p3d = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[2], 'fantasy_points_hppr'].values[shuffled_indices]))
    scored = np.array([p1d, p2d, p3d]).max(axis=0)
    
    # no shared byes
    p1a = np.column_stack((np.zeros(iterations), qbs.loc[lambda x: x.player_id == choices[0], 'fantasy_points_hppr'].values[shuffled_indices]))
    p2a= np.column_stack((qbs.loc[lambda x: x.player_id == choices[1], 'fantasy_points_hppr'].values[shuffled_indices], np.zeros(iterations)))
    tmp = qbs.loc[lambda x: x.player_id == choices[2], 'fantasy_points_hppr'].values[shuffled_indices]
    p3a = np.hstack((tmp[:, :2], np.zeros((iterations, 1)), tmp[:, 2:]))
    scorea = np.array([p1a, p2a, p3a]).max(axis=0)
    
    vals.append({'same': score.sum(axis=1).mean(), '1diff': scored.sum(axis=1).mean(), 'adiff': scorea.sum(axis=1).mean()})

# COMMAND ----------

# DBTITLE 1,Results: 3 QB bye impact
pd.DataFrame(vals).describe()