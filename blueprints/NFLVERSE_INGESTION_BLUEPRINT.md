# NFLverse Ingestion Blueprint

## Status
- State: In Progress
- Last Updated: 2026-07-18
- Owner: GitHub Copilot + Project Maintainer

## Progress Log
- 2026-07-18: Completed N1 package foundation with module scaffolding and top-level exports.
- 2026-07-18: Completed N2 wrappers in `NflverseApiClient` for all mandatory nflreadpy loader methods.
- 2026-07-18: Completed N3 contracts and validation for NFL-only wrapper entities.
- 2026-07-18: Completed N4 transform layer to deterministic Polars frames with `nvnfl_` prefixes.
- 2026-07-18: Completed N5 storage adapters for Polars outputs and Iceberg dry-run idempotency flow.
- 2026-07-18: Completed N6 pipeline orchestration with `PipelineConfig`, extraction, transform, and persistence routing.
- 2026-07-18: Completed N7 standardization integration toggles with queue/rescue artifact pass-through.
- 2026-07-18: Completed N8 initial docs and tests for wrappers, transforms, storage, and pipeline integration.

## Locked Decisions
1. Core stack remains Polars plus PyIceberg.
2. Deliverable is library-only APIs with no CLI/GUI runtime coupling.
3. nflreadpy is the canonical ingestion dependency for nflverse datasets.
4. Wrapper architecture should conform to the patterns already used by nfl.yahoo_fantasy and nfl.fantasypros_fantasy.
5. Downstream identity standardization should integrate with nfl.entity_standardization.
6. Python support target is 3.12+.
7. Scope is NFL-only.
8. The v1 wrapper surface must include all mandatory core nflreadpy loading datasets listed in this blueprint.
9. Iceberg namespaces are `nvnfl` for NFL entities and `nvcommon` for shared entities.

## Objective
Create an nflverse ingestion library component that wraps nflreadpy in a stable, testable adapter layer and exposes normalized, contract-validated outputs through the same architecture style used by the Yahoo and FantasyPros libraries.

## Proposed Package
- nfl.nflverse_fantasy

Submodules:
1. nfl.nflverse_fantasy.api
2. nfl.nflverse_fantasy.models.common
3. nfl.nflverse_fantasy.models.nfl
4. nfl.nflverse_fantasy.validation
5. nfl.nflverse_fantasy.transforms
6. nfl.nflverse_fantasy.storage.polars
7. nfl.nflverse_fantasy.storage.iceberg
8. nfl.nflverse_fantasy.pipeline
9. tests

## Wrapper Design Principles
1. All direct nflreadpy calls are isolated to api wrappers.
2. Wrapper outputs are normalized to explicit contracts and datatypes.
3. No raw DataFrame leakage across module boundaries.
4. Deterministic, schema-stable Polars outputs for all supported entities.
5. Provider-specific behavior stays in api wrappers, not in transforms or storage.

## Canonical nflreadpy Wrapper Surface

### Primary Wrapper Class
- NflverseApiClient

### Wrapped Methods (v1)
1. load_pbp wrapper for play-by-play data.
2. load_player_stats wrapper for player game or season statistics.
3. load_team_stats wrapper for team game or season statistics.
4. load_schedules wrapper for game schedules and results.
5. load_players wrapper for player information.
6. load_rosters wrapper for team rosters.
7. load_rosters_weekly wrapper for team rosters by season-week.
8. load_snap_counts wrapper for snap counts.
9. load_nextgen_stats wrapper for advanced nextgen stats.
10. load_ftn_charting wrapper for charted stats.
11. load_participation wrapper for historical participation data.
12. load_draft_picks wrapper for draft picks.
13. load_injuries wrapper for injury and practice participation statuses.
14. load_contracts wrapper for historical contract data.
15. load_officials wrapper for game officials.
16. load_combine wrapper for combine results.
17. load_depth_charts wrapper for depth chart data.
18. load_trades wrapper for trade data.
19. load_ff_playerids wrapper for ffverse/dynastyprocess ids.
20. load_ff_rankings wrapper for fantasypros rankings.
21. load_ff_opportunity wrapper for expected yards/TD/fantasy points.

Each wrapper method should:
1. Fetch via nflreadpy.
2. Convert to list-of-dicts.
3. Normalize field names.
4. Attach extraction metadata such as source, season, loaded_at.
5. Validate against contracts before returning.

## Data Contracts

### Common Entities
1. nflv_player
2. nflv_team
3. nflv_source_id_map

### NFL Entities
1. nflv_roster_weekly
2. nflv_player_stats_weekly
3. nflv_depth_chart
4. nflv_schedule_game
5. nflv_pbp
6. nflv_player_stats
7. nflv_team_stats
8. nflv_rosters
9. nflv_snap_counts
10. nflv_nextgen_stats
11. nflv_ftn_charting
12. nflv_participation
13. nflv_draft_picks
14. nflv_injuries
15. nflv_contracts
16. nflv_officials
17. nflv_combine
18. nflv_trades
19. nflv_ff_rankings
20. nflv_ff_opportunity

Each contract should define:
1. required fields
2. optional fields
3. primary key
4. allowed value constraints where needed

## Integration with Entity Standardization
1. Feed player, team, position fields through nfl.entity_standardization in pipeline mode.
2. Persist standardization artifacts alongside nflverse outputs:
   1. std_standardized_outputs
   2. std_match_queue
   3. std_rescued_records
   4. std_source_to_canonical_map
3. Do not fail pipeline on unresolved matches.

## Transform Layer
1. Convert wrapper records to typed Polars frames.
2. Enforce deterministic ordering by primary key.
3. Enforce coercion rules for numeric, boolean, and date columns.
4. Emit canonical frame names aligned to existing conventions, example nflv_player_stats_weekly.

## Storage Layer

### Polars Persistence
1. Write frames to parquet/csv/ndjson.
2. Deterministic file naming by entity.

### Iceberg Persistence
1. Use sql catalog defaults consistent with repository patterns.
2. Namespace convention:
   1. nflverse common tables: nvcommon
   2. nflverse nfl tables: nvnfl
3. Upsert mode dedupe by contract primary keys.
4. Idempotency ledger for replay-safe writes.

## Public API Surface

### Config
- PipelineConfig

Fields should include:
1. seasons and/or weeks selection.
2. enabled entities.
3. storage targets none, polars, iceberg, both.
4. standardization enable toggle.
5. standardization config pass-through.
6. dry-run controls for persistence.

### Orchestration
- run_pipeline

Behavior:
1. extract from wrappers
2. normalize and validate
3. transform to Polars frames
4. optionally standardize
5. optionally persist
6. return structured result with frames and persistence outputs

## Milestone Plan

### Milestone N1: Package Foundation
1. Scaffold nfl.nflverse_fantasy package.
2. Add pyproject dependencies if missing.
3. Add base tests and import checks.

### Milestone N2: Wrapper API Layer
1. Implement NflverseApiClient.
2. Add wrappers for all mandatory nflreadpy loading functions listed in this blueprint.
3. Add unit tests with monkeypatched nflreadpy calls.

### Milestone N3: Contracts and Validation
1. Define models.common and models.nfl contracts.
2. Implement validation module and tests.

### Milestone N4: Transform Layer
1. Implement transforms with type coercion and deterministic sorting.
2. Add transform tests with representative fixtures.

### Milestone N5: Storage Layer
1. Implement Polars writer.
2. Implement Iceberg writer with idempotency.
3. Add storage tests for dry-run and replay behavior.

### Milestone N6: Pipeline Orchestration
1. Implement run_pipeline and result objects.
2. Add integration tests for none and both persistence modes.

### Milestone N7: Standardization Integration
1. Integrate nfl.entity_standardization into nflverse pipeline.
2. Include queue and rescued outputs.
3. Add tests for low-confidence routing behavior.

### Milestone N8: Documentation and Operational Guide
1. Add README quickstart examples.
2. Add queue administration guidance for end users.
3. Add blueprint progress log updates.

## Test Matrix

### Unit Tests
1. nflreadpy wrapper correctness and normalization.
2. contract validation and key uniqueness checks.
3. mapping and coercion rules.

### Transform Tests
1. deterministic sorting.
2. null/required field handling.
3. schema stability.

### Persistence Tests
1. Polars format outputs.
2. Iceberg idempotency dry-run behavior.

### Integration Tests
1. end-to-end pipeline extraction to frame generation.
2. persistence target combinations.
3. standardization-enabled pipeline path.

## Risk Controls
1. Wrapper-only nflreadpy access to control upstream API drift.
2. Contract-first boundaries between extraction and transforms.
3. Replay-safe idempotency for persistence.
4. Non-failing unresolved standardization path with queue/rescue handling.
5. Versioned extraction metadata for reproducibility.

## Acceptance Criteria
1. nflreadpy interactions are fully encapsulated in wrapper APIs.
2. Package structure mirrors yahoo and fantasypros library patterns.
3. Outputs are contract-validated and deterministic.
4. Standardization integration emits queue/rescue artifacts without pipeline failure.
5. Both Polars and Iceberg persistence paths are available and tested.
6. NFL-only scope is enforced.
7. All mandatory nflreadpy loading datasets are wrapped and tested in v1.

## Open Questions
- None currently blocking implementation.
