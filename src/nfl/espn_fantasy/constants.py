"""ESPN Fantasy Football API constants.

Maps ESPN's numeric identifiers to human-readable names for positions,
teams, stat categories, and slot types.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ESPN Position IDs
# ---------------------------------------------------------------------------
POSITION_MAP: dict[int, str] = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "DST",
}

# Slot IDs used in the x-fantasy-filter to request specific positions
SLOT_IDS: dict[str, int] = {
    "QB": 0,
    "RB": 2,
    "WR": 4,
    "TE": 6,
    "FLEX": 23,
    "DST": 16,
    "K": 17,
}

# All fantasy-relevant slot IDs
ALL_FANTASY_SLOT_IDS: list[int] = [0, 2, 4, 6, 16, 17]

# ---------------------------------------------------------------------------
# ESPN Pro Team IDs
# ---------------------------------------------------------------------------
TEAM_MAP: dict[int, str] = {
    1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE",
    6: "DAL", 7: "DEN", 8: "DET", 9: "GB", 10: "TEN",
    11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA",
    16: "MIN", 17: "NE", 18: "NO", 19: "NYG", 20: "NYJ",
    21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC", 25: "SF",
    26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX",
    33: "BAL", 34: "HOU",
}

# ---------------------------------------------------------------------------
# ESPN Stat Category IDs → Column Names
# ---------------------------------------------------------------------------
# Passing
STAT_MAP: dict[str, str] = {
    "0": "pass_att",
    "1": "pass_cmp",
    "3": "pass_yds",
    "4": "pass_td",
    "19": "pass_int",
    "20": "pass_sack",
    # Rushing
    "23": "rush_att",
    "24": "rush_yds",
    "25": "rush_td",
    # Receiving
    "41": "rec_tgt",
    "42": "rec_yds",
    "43": "rec_td",
    "53": "receptions",
    "58": "rec_yds_after_catch",
    # Fumbles
    "68": "fumbles",
    "72": "fumbles_lost",
    # Kicking
    "77": "fg_att",
    "78": "fg_made",
    "85": "fg_missed",
    "86": "xp_att",
    "87": "xp_made",
    # DST
    "89": "dst_int",
    "90": "dst_fumble_rec",
    "91": "dst_blocked_kick",
    "92": "dst_safety",
    "93": "dst_sack",
    "95": "dst_td",
    "96": "dst_pts_allowed",
    "99": "dst_yds_allowed",
}

# ---------------------------------------------------------------------------
# Stat source and split type identifiers
# ---------------------------------------------------------------------------
STAT_SOURCE_ACTUAL = 0
STAT_SOURCE_PROJECTED = 1

STAT_SPLIT_SEASON = 0
STAT_SPLIT_WEEKLY = 1
STAT_SPLIT_LAST_7 = 2
STAT_SPLIT_LAST_15 = 3
STAT_SPLIT_LAST_30 = 4

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------
ESPN_API_BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
DEFAULT_BATCH_SIZE = 1000
MAX_PLAYERS = 5000
