# FantasyPros Fantasy Integration Blueprint

## Status
- State: Milestones 1-7 Complete
- Last Updated: 2026-07-18
- Owner: GitHub Copilot + Project Maintainer

## Locked Decisions
1. Core stack: `polars` + `pyiceberg`.
2. Deliverable: library only (no CLI, no GUI).
3. Primary v1 scope: NFL.
4. Source behavior baseline: `fantasypros_data_loader.py`.
5. Package path: `nfl.fantasypros_fantasy`.
6. Architecture pattern: contracts -> extraction -> transforms -> optional persistence -> pipeline.
7. Python support: 3.12+.
8. Include formal test matrix and release checklist.

## Integration Objective
Create a first-class `fantasypros_fantasy` sublibrary inside `nfl` that:
- extracts and normalizes FantasyPros NFL ADP/player data,
- preserves the current ADP and FP-to-Yahoo crosswalk semantics,
- standardizes transforms on Polars,
- supports optional persistence to Polars files and Iceberg,
- and provides importable pipeline APIs rather than notebook-coupled execution.

## Target Architecture
1. `nfl.fantasypros_fantasy.api`
2. `nfl.fantasypros_fantasy.models.common`
3. `nfl.fantasypros_fantasy.models.nfl`
4. `nfl.fantasypros_fantasy.validation`
5. `nfl.fantasypros_fantasy.transforms`
6. `nfl.fantasypros_fantasy.storage.polars`
7. `nfl.fantasypros_fantasy.storage.iceberg`
8. `nfl.fantasypros_fantasy.pipeline`
9. `tests/`

## Milestone Plan

### Milestone 1: Foundation and Contracts
- Scaffold `nfl.fantasypros_fantasy` package structure.
- Define canonical contracts for `fp_player`, `fp_adp_snapshot`, and `fp_yahoo_player_map`.
- Implement reusable record/frame validation and PK uniqueness checks.
- Add initial contract validation tests.

Acceptance criteria:
- Package imports cleanly from `nfl.fantasypros_fantasy`.
- Contract validation catches missing required fields and duplicate primary keys.

### Milestone 2: FantasyPros API Extraction Layer
- Build `FantasyProsApiClient` around HTTP + HTML parsing.
- Support historical/current season ADP page variants.
- Normalize player and ADP rows into contract-shaped records.
- Add robust parsing guards and actionable extraction errors.

Acceptance criteria:
- Extraction succeeds for fixture-backed page samples.
- Normalized output passes contract validation.

### Milestone 3: Crosswalk Matching Service
- Implement FP-to-Yahoo player matching as reusable library logic.
- Preserve existing priority semantics (exact before fuzzy; ADP rank tie-break).
- Enforce bidirectional 1:1 mapping guarantees.
- Abstract Yahoo player source behind a provider interface.

Acceptance criteria:
- Matching logic is unit-tested and deterministic.
- Duplicate/collision scenarios are handled without violating 1:1 constraints.

### Milestone 4: Polars Transform Layer
- Convert normalized records to typed Polars frames.
- Apply explicit coercion and deterministic sorting by primary keys.
- Re-run contract checks post-transform.

Acceptance criteria:
- Transform outputs are stable and contract-compliant.
- Invalid records raise actionable transform/validation errors.

### Milestone 5: Persistence Adapters
- Add local Polars persistence writer (parquet/csv/ndjson).
- Add Iceberg persistence with idempotency controls and namespace resolution.
- Keep write behavior safe by default (dry-run where appropriate).

Acceptance criteria:
- Persisted outputs match expected schemas and row counts.
- Repeated writes are idempotent under unchanged payloads.

### Milestone 6: Public Pipeline API
- Implement config + orchestration entrypoint for end-to-end runs.
- Support extraction-only, transform-only, and persist-enabled modes.
- Expose extension points for dependency injection in tests/consumers.

Acceptance criteria:
- Consumers can run workflow via imports only.
- Pipeline result object returns frames and persistence outcomes.

### Milestone 7: Notebook Logic Migration and Cutover
- Decompose `fantasypros_data_loader.py` into library-compatible components.
- Convert former notebook views into materialized tables generated directly by the library pipeline.
- Document migration from notebook workflow to library workflow.

Acceptance criteria:
- Core library has no Databricks runtime dependency.
- Existing notebook semantics are represented in documented migration steps.

## Risk Controls
1. Contract-first development to prevent schema drift.
2. Parser layout detection + fixture coverage to protect against HTML changes.
3. Primary-key and null validations at normalization and transform boundaries.
4. Deterministic ranking and tie-break rules for player crosswalks.
5. Keep core library engine-agnostic with no Spark/Databricks runtime dependency.
6. Idempotent persistence to avoid duplicate historical writes.

## Test Matrix

### Unit Tests
- Contract validation (required/optional fields, PK uniqueness).
- HTML parser behaviors across page layout variants.
- Matching strategy correctness for exact/fuzzy/collision scenarios.

### Transformation Tests
- Type coercion and deterministic ordering.
- Contract conformance after conversion to Polars.

### Persistence Tests
- Polars writer format coverage.
- Iceberg namespace/idempotency behavior.

### Integration Tests
- End-to-end pipeline using fixture HTML + mocked Yahoo provider.
- Incremental re-run behavior and idempotent outcomes.

### Regression Tests
- Compare extracted/normalized ADP fields against baseline expectations from notebook behavior.

## Release Checklist
1. Python requirement verified at 3.12+.
2. Scraping dependencies declared (`beautifulsoup4`, `lxml`) in project metadata.
3. Tests/type/lint gates green.
4. Pipeline API documented with quickstart examples.
5. Migration notes from notebook workflow completed.
6. Version tagging and package release steps prepared.

## Open Configuration Decisions
- None currently blocking Milestone 7.

## Progress Tracking

### Cadence
- Update this file after each completed milestone, and after any major scope/risk change.
- Each update should include date, summary, decisions, blockers, and next actions.

### Progress Log

#### 2026-07-18 - Blueprint Created
- Summary:
  - Created FantasyPros integration blueprint modeled after the Yahoo blueprint process.
  - Captured architecture, milestone plan, risk controls, and test strategy.
- Decisions captured:
  - Build as `nfl.fantasypros_fantasy` within the existing `nfl` package.
  - Keep v1 focused on NFL ADP + FP-to-Yahoo mapping behavior.
- Blockers:
  - None.
- Next actions:
  1. Continue Milestone 2 implementation for extraction client and parser normalization.

#### 2026-07-18 - Milestone 1 Completed
- Summary:
  - Scaffolded `src/nfl/fantasypros_fantasy` package and `models` namespace.
  - Added canonical contracts and validation module.
  - Added tests in `tests/test_fp_validation_contracts.py`.
  - Exported sublibrary in top-level `nfl` package.
- Decisions captured:
  - Contract-first validation mirrors `yahoo_fantasy` conventions for consistency.
- Blockers:
  - None.
- Next actions:
  1. Start Milestone 2: create `fantasypros_fantasy.api` and fixture-driven parsing tests.

#### 2026-07-18 - Milestone 2 Completed
- Summary:
  - Implemented `nfl.fantasypros_fantasy.api` with `FantasyProsApiClient` and robust ADP page parsing.
  - Added support for both historical multi-platform and current-season ADP page layouts.
  - Normalized extracted player + ADP rows to contract-shaped outputs with optional validation.
  - Added API parsing tests in `tests/test_fp_api.py`.
- Decisions captured:
  - Extraction raises explicit `ExtractionError` when expected table structure is missing.
  - ADP extraction keeps current-season fallback behavior when only consensus ADP is present.
- Blockers:
  - None.
- Next actions:
  1. Implement Milestone 3 crosswalk matching service.

#### 2026-07-18 - Milestone 3 Completed
- Summary:
  - Implemented `nfl.fantasypros_fantasy.matching.build_fp_yahoo_crosswalk`.
  - Preserved match priority behavior (exact before fuzzy) with ADP-rank tie-breaking.
  - Enforced bidirectional 1:1 mapping behavior.
  - Added crosswalk tests in `tests/test_fp_matching.py`.
- Decisions captured:
  - Normalization strips punctuation/case for stable name matching.
  - Fuzzy matching uses last-name + first three chars + same position.
- Blockers:
  - None.
- Next actions:
  1. Implement Milestone 4 Polars transform layer.

#### 2026-07-18 - Milestone 4 Completed
- Summary:
  - Implemented `nfl.fantasypros_fantasy.transforms` with contract-aware entity transforms.
  - Added deterministic primary-key sorting and shared type coercion rules.
  - Added transform validation errors with actionable diagnostics.
  - Added transform tests in `tests/test_fp_transforms.py`.
- Decisions captured:
  - Common and NFL-scoped entities are emitted as separate frame namespaces.
- Blockers:
  - None.
- Next actions:
  1. Implement Milestone 5 persistence adapters.

#### 2026-07-18 - Milestone 5 Completed
- Summary:
  - Implemented `nfl.fantasypros_fantasy.storage.polars.persist_with_polars`.
  - Implemented `nfl.fantasypros_fantasy.storage.iceberg.persist_to_iceberg` with namespace resolution, upsert dedupe, and idempotency.
  - Added Iceberg adapter tests in `tests/test_fp_iceberg_storage.py`.
- Decisions captured:
  - Default Iceberg namespaces set to `fpnfl` for NFL entities and `fpcommon` for shared entities.
- Blockers:
  - None.
- Next actions:
  1. Implement Milestone 6 public pipeline orchestration.

#### 2026-07-18 - Milestone 6 Completed
- Summary:
  - Implemented `nfl.fantasypros_fantasy.pipeline` with `PipelineConfig`, `PipelineRunResult`, and `run_pipeline`.
  - Wired extraction, optional crosswalk matching, transforms, and optional persistence (`none`, `polars`, `iceberg`, `both`).
  - Added pipeline tests in `tests/test_fp_pipeline.py`.
  - Updated package exports and project dependencies for scraping runtime requirements.
- Decisions captured:
  - Pipeline remains library-first with dependency-injection support for testable clients.
- Blockers:
  - None.
- Next actions:
  1. Start Milestone 7 documentation and notebook migration notes.

#### 2026-07-18 - Milestones 1-6 Test Verification
- Summary:
  - Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
  - Result: `31 passed in 1.59s`.
- Decisions captured:
  - The new FantasyPros modules are stable alongside existing Yahoo modules.
- Blockers:
  - None.
- Next actions:
  1. Complete Milestone 7 docs and migration notes.

#### 2026-07-18 - Milestone 7 Completed
- Summary:
  - Added `FANTASY_PROS_NOTEBOOK_MIGRATION.md` documenting notebook-to-library mapping and cutover guidance.
  - Updated `README.md` with `nfl.fantasypros_fantasy` quickstart and blueprint/migration references.
  - Confirmed core `fantasypros_fantasy` library has no Databricks runtime dependency.
  - Converted the former current ADP view shape into a materialized pipeline table (`nfl_fp_current_adp`).
- Decisions captured:
  - Spark is not part of the target architecture; analytics projections are delivered as materialized tables.
- Blockers:
  - None.
- Next actions:
  1. Optional follow-up: add PyIceberg materialization helpers for table/view-like analytics artifacts.

## Change Log
- 2026-07-18: File created with initial approved FantasyPros integration blueprint.
- 2026-07-18: Milestone 1 completion logged with contract/validation scaffolding and tests.
- 2026-07-18: Milestones 2-6 implemented (API, matching, transforms, storage, pipeline) with passing tests.
- 2026-07-18: Milestone 7 completed with notebook migration documentation and README updates.
