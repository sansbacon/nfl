"""Fantasy Life (FL) data source package.

Provides CSV rankings parsing, HTML player-ID extraction, crosswalk
matching, and Ibis-based transforms for persisting FL data.

Usage::

    from nfl.fantasylife_fantasy.pipeline import PipelineConfig, run_pipeline

    result = run_pipeline(PipelineConfig(
        season=2026,
        rankings_csv_path="/Volumes/nfl/fl/fl_volume/incoming/rankings/fantasy_life_rankings_20260811.csv",
        html_paths=["/Volumes/nfl/fl/fl_volume/incoming/html/flife1.html", ...],
    ))
"""
