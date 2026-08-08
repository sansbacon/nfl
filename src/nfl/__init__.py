"""Top-level nfl package.

Sub-packages:
- common: shared utilities (matching, crosswalk, storage)
- yahoo_fantasy: Yahoo Fantasy API extraction and transforms
- fantasypros_fantasy: FantasyPros scraping and transforms
- espn_fantasy: ESPN public API extraction and transforms
- sleeper_fantasy: Sleeper public API extraction and transforms
- nflverse_fantasy: NFLverse data ingestion
- entity_standardization: cross-source entity resolution
"""

__all__ = [
    "common",
    "entity_standardization",
    "espn_fantasy",
    "fantasypros_fantasy",
    "nflverse_fantasy",
    "sleeper_fantasy",
    "yahoo_fantasy",
]

