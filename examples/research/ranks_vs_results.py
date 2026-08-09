# Databricks notebook source
# DBTITLE 1,Ranks vs Results
# MAGIC %md
# MAGIC ## Ranks vs. Results: Fantasy Pros
# MAGIC
# MAGIC Compares pre-season expert consensus rankings against actual weekly player results
# MAGIC across seasons 2016-2020. Scrapes FantasyPros weekly leaders and weekly consensus rankings,
# MAGIC then measures rank accuracy by position.
# MAGIC
# MAGIC > **Note:** Migrated from `ffdatwarehouse/research/`. Originally run 2021-09-09.
# MAGIC > Uses deprecated `/dbfs/FileStore/eric/stats/` paths and direct FantasyPros scraping.
# MAGIC > Consider updating to use `nfl.fantasypros_fantasy` pipeline + UC tables.

# COMMAND ----------

# DBTITLE 1,Imports
import json
from pathlib import Path

import pandas as pd
import requests

# COMMAND ----------

# DBTITLE 1,Data paths (LEGACY)
# TODO: Update paths to use UC volumes or nfl library
# raw = Path('/dbfs/FileStore/eric/stats/raw')
# processed = Path('/dbfs/FileStore/eric/stats/processed')
raise NotImplementedError('Update data source paths — /dbfs/FileStore/ is deprecated')

# COMMAND ----------

# DBTITLE 1,Team code standardization
TEAM_CODES = {
  'ARI': ['ari', 'ARZ', 'CRD', 'Arizona Cardinals', 'Cardinals', 'Arizona', 'crd'],
  'ATL': ['FAL', 'Atlanta Falcons', 'Falcons', 'Atlanta', 'atl'],
  'BAL': ['RAV', 'Baltimore Ravens', 'Ravens', 'Baltimore', 'rav'],
  'BUF': ['BIL', 'Buffalo Bills', 'Bills', 'Buffalo', 'buf'],
  'CAR': ['Carolina Panthers', 'Panthers', 'Carolina', 'car'],
  'CHI': ['Chicago Bears', 'Bears', 'Chicago', 'chi'],
  'CIN': ['CIN', 'Cincinnati Bengals', 'Bengals', 'Cincinnati', 'cin'],
  'CLE': ['CLE', 'Cleveland Browns', 'Browns', 'Cleveland', 'cle'],
  'DAL': ['DAL', 'Dallas Cowboys', 'Cowboys', 'Dallas', 'dal'],
  'DEN': ['DEN', 'Denver Broncos', 'Broncos', 'Denver', 'den'],
  'DET': ['DET', 'Detroit Lions', 'Lions', 'Detroit', 'det'],
  'GB': ['GNB', 'Green Bay Packers', 'Packers', 'Green Bay', 'gnb'],
  'HOU': ['HTX', 'Houston Texans', 'Texans', 'Houston', 'htx'],
  'IND': ['CLT', 'Indianapolis Colts', 'Colts', 'Indianapolis', 'clt'],
  'JAX': ['JAX', 'Jacksonville Jaguars', 'Jaguars', 'Jacksonville', 'jax'],
  'KC': ['KAN', 'Kansas City Chiefs', 'Chiefs', 'Kansas City', 'kan'],
  'LAC': ['SDG', 'Los Angeles Chargers', 'Chargers', 'LA Chargers', 'sdg', 'San Diego'],
  'LAR': ['RAM', 'Los Angeles Rams', 'Rams', 'LA Rams', 'ram', 'St. Louis'],
  'LV': ['RAI', 'Las Vegas Raiders', 'Raiders', 'Las Vegas', 'rai', 'Oakland'],
  'MIA': ['MIA', 'Miami Dolphins', 'Dolphins', 'Miami', 'mia'],
  'MIN': ['MIN', 'Minnesota Vikings', 'Vikings', 'Minnesota', 'min'],
  'NE': ['NWE', 'New England Patriots', 'Patriots', 'New England', 'nwe'],
  'NO': ['NOR', 'New Orleans Saints', 'Saints', 'New Orleans', 'nor'],
  'NYG': ['NYG', 'New York Giants', 'Giants', 'NY Giants', 'nyg'],
  'NYJ': ['NYJ', 'New York Jets', 'Jets', 'NY Jets', 'nyj'],
  'PHI': ['PHI', 'Philadelphia Eagles', 'Eagles', 'Philadelphia', 'phi'],
  'PIT': ['PIT', 'Pittsburgh Steelers', 'Steelers', 'Pittsburgh', 'pit'],
  'SEA': ['SEA', 'Seattle Seahawks', 'Seahawks', 'Seattle', 'sea'],
  'SF': ['SFO', 'San Francisco 49ers', '49ers', 'San Francisco', 'sfo'],
  'TB': ['TAM', 'Tampa Bay Buccaneers', 'Buccaneers', 'Tampa Bay', 'tam'],
  'TEN': ['OTI', 'Tennessee Titans', 'Titans', 'Tennessee', 'oti'],
  'WAS': ['WAS', 'Washington', 'was', 'Washington Football Team', 'Commanders'],
}

# COMMAND ----------

# DBTITLE 1,Scrape weekly player results
# Scrapes FantasyPros weekly leaders pages (2012-2020)
# base_url = 'https://www.fantasypros.com/nfl/reports/leaders/{}.php'
# for year in range(2012, 2021):
#     for week in range(1, 18):
#         for page in ('qb', 'ppr-rb', 'ppr-wr', 'ppr-te', 'dst', 'k'):
#             fn = raw / f'{year}_{week}_{page}.html'
#             if fn.is_file():
#                 continue
#             params = {'year': year, 'start': week, 'end': week}
#             r = requests.get(base_url.format(page), params=params, headers=headers)
#             fn.write_text(r.text)

# COMMAND ----------

# DBTITLE 1,Fetch weekly rankings from API
# Uses FantasyPros API for weekly consensus rankings (2016-2020)
# base_url = 'https://api.fantasypros.com/v2/json/nfl/{}/consensus-rankings'
# positions = ('QB', 'RB', 'WR', 'TE', 'FLX', 'DST')
# for year in range(2016, 2021):
#     for week in range(1, 18):
#         for pos in positions:
#             fn = raw / f'{year}_{week}_{pos}.json'
#             if fn.is_file():
#                 continue
#             params = {'year': year, 'week': week, 'position': pos, 'scoring': 'PPR'}
#             r = requests.get(base_url.format(year), params=params, headers=headers)
#             fn.write_text(r.text)