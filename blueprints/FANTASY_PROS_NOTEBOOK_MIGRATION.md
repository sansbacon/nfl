# FantasyPros Notebook Migration Guide

This guide maps the Databricks notebook workflow in fantasypros_data_loader.py to the new library workflow in nfl.fantasypros_fantasy.

## Scope
- Source workflow: Databricks notebook with Spark SQL DDL/merge steps.
- Target workflow: importable Python library orchestration.
- v1 sport scope: NFL.
- Standardization target: Polars + PyIceberg only (no Spark runtime dependency).

## Function Mapping

Notebook function: create_fp_tables
Library equivalent: no direct core equivalent
Notes: Table materialization is an optional PyIceberg-oriented concern outside core pipeline.

Notebook function: create_fp_views
Library equivalent: pipeline materialized table `nfl_fp_current_adp`
Notes: The former current ADP view is now emitted as a table-shaped frame and persisted through standard library persistence targets.

Notebook function: load_dim_fp_players
Library equivalent: FantasyProsApiClient.get_players + transforms.transform
Notes: player extraction and normalization are now separate from persistence.

Notebook function: load_fact_fp_adp
Library equivalent: FantasyProsApiClient.get_adp_snapshots + transforms.transform
Notes: ADP normalization and quality checks are contract-driven.

Notebook function: load_fact_fp_yh_players
Library equivalent: matching.build_fp_yahoo_crosswalk
Notes: 1:1 mapping logic and exact/fuzzy priority are implemented as reusable library code.

## End-to-End Pipeline Mapping

Notebook flow:
1. Build/load widgets and runtime config.
2. Create base/derived tables through library pipeline + persistence targets.
3. Scrape FantasyPros HTML.
4. Merge player/adp facts.
5. Build FP-to-Yahoo crosswalk table.

Library flow:
1. Construct PipelineConfig.
2. Provide season and optional Yahoo player records.
3. Run run_pipeline for extraction, matching, transform, and optional persistence.
4. Consume returned Polars frames and write results to configured targets.

## Minimal Library Example

```python
from datetime import date

from nfl.fantasypros_fantasy import PipelineConfig, run_pipeline

yahoo_players = [
    {
        "yahoo_player_id": 1001,
        "full_name": "Justin Jefferson",
        "first_name": "Justin",
        "last_name": "Jefferson",
        "display_position": "WR",
    }
]

result = run_pipeline(
    season=2025,
    yahoo_players=yahoo_players,
    config=PipelineConfig(
        storage_target="both",
        effective_date=date(2026, 7, 18),
        polars_output_dir="./output/fantasypros_polars",
        iceberg_dry_run=True,
    ),
)

print(result.frames.keys())
print(result.polars_outputs)
```

## What Moved Out Of Core Library
- Databricks widget setup.
- Engine-specific SQL DDL lifecycle management.
- Engine-specific MERGE/INSERT orchestration.

These concerns can be implemented as optional PyIceberg-oriented integration helpers that call the core library.

## Validation and Determinism Guarantees
- Contract-first validation for all supported entities.
- Deterministic frame ordering by entity primary key.
- Idempotent Iceberg persistence support for replay safety.

## Recommended Next Step
- Add additional materialized analytics tables in pipeline as needed, then persist with existing Polars/PyIceberg adapters.
