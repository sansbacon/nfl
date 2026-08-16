"""Fantasy Points (FPTS) data source package.

Provides CSV rankings parsing, crosswalk matching, and Ibis-based
transforms for persisting Fantasy Points redraft PPR rankings data.

Usage::

    from nfl.fantasypoints_fantasy.pipeline import PipelineConfig, run_pipeline

    result = run_pipeline(PipelineConfig(
        season=2026,
        rankings_csv_path="/Volumes/nfl/fpts/fpts_volume/incoming/ranks/rankings.redraft.barrett.csv",
    ))
"""
