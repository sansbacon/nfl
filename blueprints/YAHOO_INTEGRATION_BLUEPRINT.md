# Yahoo Fantasy Unified Library Blueprint

## Status
- State: Milestone G Complete
- Last Updated: 2026-07-18
- Owner: GitHub Copilot + Project Maintainer

## Locked Decisions
1. Core stack: `polars` + `pyiceberg`.
2. Deliverable: library only (no CLI, no GUI).
3. Data model strategy: keep sports separate.
4. Behavioral source of truth: `yahoo` codebase.
5. Package name: `yahoo_fantasy`.
6. Legacy JSON output compatibility: not required.
7. Legacy entrypoints/scripts: remove immediately.
8. Python support: 3.12+.
9. Include formal test matrix and release checklist.
10. PyIceberg catalog type: `sql`.
11. Iceberg namespace convention: `yhnfl` (NFL), `ynbna` (NBA).

## Integration Objective
Merge `yahoo` and `yh` into one coherent Python library that:
- uses Yahoo behavior as the canonical implementation baseline,
- standardizes transforms on Polars,
- persists analytical datasets to Iceberg using PyIceberg,
- keeps sport-specific datasets separate,
- and removes app-style entrypoints in favor of importable library APIs.

## Target Architecture
1. `yahoo_fantasy.auth`
2. `yahoo_fantasy.api`
3. `yahoo_fantasy.models.nfl`
4. `yahoo_fantasy.models.nba`
5. `yahoo_fantasy.transforms`
6. `yahoo_fantasy.storage.iceberg`
7. `yahoo_fantasy.storage.polars`
8. `yahoo_fantasy.pipeline`
9. `yahoo_fantasy.validation`
10. `tests/`

## Milestone Plan

### Milestone A: Foundation and Packaging
- Create unified `yahoo_fantasy` package scaffold.
- Enforce Python 3.12+ in project metadata.
- Remove CLI/GUI and executable script entrypoints.
- Set linting, formatting, and type-check baselines.

Acceptance criteria:
- Package imports cleanly in fresh Python 3.12 env.
- No runtime references to CLI/GUI modules.

### Milestone B: Canonical Data Contracts
- Define canonical entities across leagues/teams/players/core facts.
- Define sport-specific contracts for NFL/NBA.
- Freeze field names, key semantics, and required vs optional columns.

Acceptance criteria:
- All extracted datasets map to typed contracts.
- No cross-sport schema mixing.

### Milestone C: Yahoo API Unification
- Consolidate auth/session/token/cache behavior from `yahoo` baseline.
- Build shared endpoint adapters + normalized response mappers.
- Standardize error handling and retry semantics.

Acceptance criteria:
- API layer fetches required resources per sport.
- Normalized outputs pass contract validation.

### Milestone D: Polars Pipeline
- Implement transformations as Polars-first dataflows.
- Add explicit coercion, null policy, and quality checks.
- Produce stable, typed Polars frames per entity.

Acceptance criteria:
- End-to-end transform works per sport.
- Validation failures provide actionable diagnostics.

### Milestone E: PyIceberg Persistence
- Implement catalog/table abstraction with PyIceberg.
- Implement append/upsert rules with idempotency keys.
- Keep table namespaces separate per sport.

Acceptance criteria:
- Iceberg writes succeed with stable schema + partitioning.
- Replay of same load is idempotent.

### Milestone F: Public Library API
- Expose import-based service APIs for extraction/transform/persist.
- Add config objects and extension points.
- Document public API surface and usage patterns.

Acceptance criteria:
- Consumers can execute workflow without scripts.
- Public API documented and stable.

### Milestone G: Hard Cutover Cleanup
- Remove obsolete legacy modules and compatibility wrappers.
- Finalize docs to library-only usage.
- Prepare release artifacts.

Acceptance criteria:
- Repository has one coherent library path.
- No deprecated code paths remain.

## Risk Controls
1. Contract-first development to avoid schema drift.
2. Idempotency keys to avoid duplicate persisted records.
3. Validation at normalization and persistence boundaries.
4. Strict per-sport namespace and table separation.
5. Fixture-driven regression checks vs source-of-truth behavior.
6. Fail-fast on Iceberg schema incompatibilities.

## Test Matrix

### Unit Tests
- Auth token parsing/refresh.
- Endpoint normalization.
- Field coercion and defaults.
- Sport-specific validators.

### Transformation Tests
- NFL weekly flow correctness.
- NBA category/roto handling.
- Determinism on repeated runs.

### Persistence Tests
- Iceberg table creation and schema alignment.
- Append/upsert correctness.
- Idempotent replay behavior.
- Per-sport namespace enforcement.

### Integration Tests
- End-to-end run for one league-season per sport.
- Multi-season incremental ingestion.
- Retry/error recovery behavior.

### Regression Tests
- Compare against `yahoo` source behavior for:
  - primary key uniqueness,
  - record counts,
  - critical numeric fields.

### Performance Tests
- Throughput benchmark by dataset family.
- Memory profile on large weekly/player workloads.

## Release Checklist
1. Python requirement set to 3.12+ and verified.
2. Dependencies pinned/ranged for Polars + PyIceberg.
3. Tests/type/lint gates green.
4. Idempotency and schema evolution validated.
5. Library docs published (quickstart, API, config, troubleshooting).
6. Legacy entrypoints removed.
7. Version tagged and package artifact built.

## Open Configuration Decisions
- None.

## Progress Tracking

### Cadence
- Update this file after each completed milestone, and after any major scope/risk change.
- Each update should include date, summary, decisions, blockers, and next actions.

### Progress Log

#### 2026-07-18 - Blueprint Created
- Summary:
  - Initial integration blueprint created and approved.
  - Scope and architecture constraints locked.
- Decisions captured:
  - Library-only approach.
  - Polars + PyIceberg standardization.
  - `yahoo` as source-of-truth behavior.
  - Immediate legacy entrypoint removal plan.
- Blockers:
  - Need decision on PyIceberg catalog type.
  - Need decision on default sport namespace pattern for NFL/NBA tables.
- Next actions:
  1. Finalize open configuration decisions.
  2. Begin Milestone A implementation.

#### 2026-07-18 - Milestone A Completed
- Summary:
  - Created unified `yahoo_fantasy` package scaffold at repository root.
  - Added root project metadata with Python 3.12+ enforcement.
  - Removed CLI/GUI wrapper entrypoints and script-style package metadata.
  - Disabled direct script execution guards in legacy `yh` modules.
- Decisions captured:
  - Consolidation now centers on root `pyproject.toml` + `yahoo_fantasy` package.
  - `yh` is treated as archived reference during migration.
- Blockers:
  - Need decision on PyIceberg catalog type for Milestone E design.
  - Need decision on default Iceberg namespace convention.
- Next actions:
  1. Start Milestone B: define canonical data contracts for NFL and NBA.
  2. Add model-level validation contracts under `yahoo_fantasy.models` and `yahoo_fantasy.validation`.

#### 2026-07-18 - Milestone B Completed
- Summary:
  - Added canonical common contracts for league, team, player, draft pick, and transaction entities.
  - Added NFL and NBA sport-specific contracts with frozen required/optional fields and primary keys.
  - Implemented validation utilities for records, primary-key uniqueness, and Polars frame schema checks.
  - Added initial tests for contract validation behavior.
- Decisions captured:
  - Contract lookups now follow sport-specific-first, common-fallback resolution.
  - Key uniqueness is enforced as a first-class validation step for each entity contract.
- Blockers:
  - Need PyIceberg catalog-type decision before Milestone E persistence design hardening.
- Next actions:
  1. Start Milestone C: consolidate Yahoo API/auth/token/cache behavior into `yahoo_fantasy.api` and `yahoo_fantasy.auth`.
  2. Wire normalization outputs to Milestone B validation contracts.

#### 2026-07-18 - Milestone B Test Verification
- Summary:
  - Re-ran tests successfully using the configured Python 3.12 conda interpreter.
  - Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
  - Result: `4 passed in 0.75s`.
- Decisions captured:
  - Standard test invocation should use the environment-qualified Python command above.
- Blockers:
  - Need PyIceberg catalog-type decision before Milestone E persistence design hardening.
- Next actions:
  1. Proceed with Milestone C implementation.

#### 2026-07-18 - Milestone C Completed
- Summary:
  - Implemented `yahoo_fantasy.auth` with reusable OAuth token load/save, auth code parsing, and non-interactive session bootstrap.
  - Implemented `yahoo_fantasy.api` with a cached Yahoo API client and normalized accessors for league metadata, team metadata, draft picks, transactions, league discovery, and standings.
  - Wired normalization outputs to Milestone B contract validation for common entities and NFL/NBA standings.
  - Added unit tests for auth parsing, token-cache session bootstrap, and API normalization behavior.
- Decisions captured:
  - API access now centers on `YahooApiClient` with cache-aware GET semantics and contract validation enabled by default.
  - Library auth flow remains non-interactive unless caller explicitly supplies/open-browser OAuth bootstrap inputs.
- Blockers:
  - Need PyIceberg catalog-type decision before Milestone E persistence design hardening.
  - Need default NFL/NBA namespace convention for Iceberg tables.
- Next actions:
  1. Begin Milestone D: Polars-first transformation pipeline and quality checks.
  2. Introduce transform-level validation hooks using Milestone B contracts.

#### 2026-07-18 - Milestone D Completed
- Summary:
  - Implemented `yahoo_fantasy.transforms` with Polars-first entity transforms for common, NFL, and NBA datasets.
  - Added deterministic sort by contract primary key, shared type coercion rules, and null/required-field quality checks.
  - Added transform-level contract enforcement with actionable `TransformValidationError` diagnostics.
  - Implemented `yahoo_fantasy.storage.polars.persist_with_polars` to write transformed frames to Parquet/CSV/NDJSON.
  - Added transform tests covering coercion, determinism, validation failures, and full common+sport frame assembly.
- Decisions captured:
  - Transform outputs default to contract-allowed fields only (stable schema by default).
  - Entity validation occurs both pre-frame (records) and post-frame (Polars shape/null checks).
- Blockers:
  - Need PyIceberg catalog-type decision before Milestone E persistence design hardening.
  - Need default NFL/NBA namespace convention for Iceberg tables.
- Next actions:
  1. Begin Milestone E: implement PyIceberg catalog/table abstraction and idempotent write semantics.
  2. Align Iceberg table naming with chosen sport namespace convention.

#### 2026-07-18 - Milestone D Test Verification
- Summary:
  - Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
  - Result: `12 passed in 0.67s`.
- Decisions captured:
  - Current transform and validation behavior is stable under deterministic ordering checks.
- Blockers:
  - None new beyond open Milestone E configuration decisions.
- Next actions:
  1. Proceed to Milestone E implementation.

#### 2026-07-18 - Milestone E Completed
- Summary:
  - Implemented `yahoo_fantasy.storage.iceberg.persist_to_iceberg` with sql catalog defaults and explicit namespace resolution.
  - Added namespace mapping using `yhnfl` for NFL frames and `ynbna` for NBA frames.
  - Added upsert batch dedupe by contract primary keys and idempotency ledger-based write skipping.
  - Added dry-run support for validation and CI-safe testing.
  - Added Iceberg adapter tests covering namespace resolution and idempotency behavior.
- Decisions captured:
  - Catalog type for v1 is locked to `sql`.
  - Namespace convention is locked to `yhnfl` and `ynbna`.
- Blockers:
  - None for Milestone E implementation.
- Next actions:
  1. Begin Milestone F: expose public library orchestration APIs.
  2. Wire API extraction + transforms + storage adapters into a cohesive service layer.

#### 2026-07-18 - Milestone E Test Verification
- Summary:
  - Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
  - Result: `14 passed in 0.84s`.
- Decisions captured:
  - Iceberg adapter behavior is stable in dry-run mode with deterministic idempotency checks.
- Blockers:
  - None.
- Next actions:
  1. Proceed to Milestone F.

#### 2026-07-18 - Milestone F Completed
- Summary:
  - Implemented public orchestration API in `yahoo_fantasy.pipeline` with `PipelineConfig`, `PipelineRunResult`, and `run_pipeline`.
  - Wired end-to-end flow across API extraction, Polars transforms, and optional persistence targets (`none`, `polars`, `iceberg`, `both`).
  - Added injectable API client support for testing and embedding scenarios.
  - Added pipeline tests for no-persistence and dual-target persistence paths.
- Decisions captured:
  - Public service entrypoint for workflow orchestration is `run_pipeline`.
  - Persistence routing is configuration-driven and defaults to library-safe `storage_target="none"`.
- Blockers:
  - None for Milestone F implementation.
- Next actions:
  1. Begin Milestone G: hard cutover cleanup and finalize release readiness checks.

#### 2026-07-18 - Milestone F Test Verification
- Summary:
  - Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
  - Result: `16 passed in 0.73s`.
- Decisions captured:
  - Pipeline orchestration is stable across dry-run persistence combinations.
- Blockers:
  - None.
- Next actions:
  1. Proceed to Milestone G.

#### 2026-07-18 - Milestone G Completed
- Summary:
  - Removed obsolete legacy Python module paths from the old `yahoo` and `yh` codebases.
  - Updated package root exports in `yahoo_fantasy.__init__` for release-ready library ergonomics.
  - Added root `README.md` with library-first quickstart, persistence defaults, and test command.
  - Updated archived `yh/README.md` to reflect completed hard cutover.
- Decisions captured:
  - Legacy Python execution paths are fully retired in favor of `yahoo_fantasy` APIs.
  - Public package entrypoints are now import-first via `run_pipeline`, `PipelineConfig`, and auth/API helpers.
- Blockers:
  - None.
- Next actions:
  1. Final release step: choose version tag and publish package artifact.

#### 2026-07-18 - Milestone G Test Verification
- Summary:
  - Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
  - Result: `16 passed in 1.17s`.
- Decisions captured:
  - Post-cutover codebase remains stable after removing legacy module paths.
- Blockers:
  - None.
- Next actions:
  1. Execute release tagging/publish workflow when ready.

#### 2026-07-18 - Namespace Packaging Migration
- Summary:
  - Migrated library code to src-based namespace package layout under `src/nfl/yahoo_fantasy`.
  - Updated imports, tests, and package discovery to target `nfl.yahoo_fantasy`.
  - Added test bootstrap for src layout resolution and revalidated full suite.
- Decisions captured:
  - `nfl` is the top-level import package and `yahoo_fantasy` is a subpackage.
  - Setuptools package discovery resolves from `src` with `nfl`/`nfl.*` includes.
- Blockers:
  - None.
- Next actions:
  1. Execute release tagging/publish workflow when ready.

#### 2026-07-18 - fantasypros_fantasy Plan Approved
- Summary:
  - Approved creation of a new `nfl.fantasypros_fantasy` sublibrary modeled after `nfl.yahoo_fantasy`.
  - Confirmed architecture pattern: contracts -> extraction -> transforms -> optional persistence -> orchestration pipeline.
  - Confirmed phased execution with milestone tracking in this blueprint.
- Decisions captured:
  - Implement as a package-local sublibrary under `src/nfl/fantasypros_fantasy`.
  - Start with NFL scope and FantasyPros ADP + Yahoo crosswalk entities.
- Blockers:
  - None.
- Next actions:
  1. Implement Milestone 1 contracts and validation.

#### 2026-07-18 - fantasypros_fantasy Milestone 1 Completed
- Summary:
  - Scaffolded package root `src/nfl/fantasypros_fantasy` and `models` namespace.
  - Added canonical FantasyPros contracts for player, ADP snapshot, and Yahoo mapping entities.
  - Implemented `validation.py` with record checks, primary-key uniqueness checks, and Polars frame checks, following existing yahoo_fantasy conventions.
  - Added tests in `tests/test_fp_validation_contracts.py` for happy-path validation, required-field failures, duplicate PK rejection, and Polars frame validation.
  - Exported `fantasypros_fantasy` from top-level `nfl` package.
- Decisions captured:
  - v1 validation scope is contract-first and sport-specific overrides are extensible via `models/nfl.py`.
- Blockers:
  - None.
- Next actions:
  1. Run full test suite and verify baseline stability.
  2. Begin Milestone 2 extraction client (`fantasypros_fantasy.api`) design.

## Change Log
- 2026-07-18: File created with approved blueprint and progress tracking template.
- 2026-07-18: Milestone A completion logged; architecture numbering corrected; non-target sport planning references removed.
- 2026-07-18: Milestone B completion logged with canonical contracts, validation utilities, and initial tests.
- 2026-07-18: Milestone B tests re-verified with environment-qualified pytest command.
- 2026-07-18: Milestone C completion logged with OAuth/API client implementation and passing tests.
- 2026-07-18: Milestone D completion logged with Polars transforms, persistence helper, and passing tests.
- 2026-07-18: Milestone E completion logged with sql-catalog Iceberg adapter, namespace conventions, and passing tests.
- 2026-07-18: Milestone F completion logged with public pipeline API and passing tests.
- 2026-07-18: Milestone G completion logged with hard cutover cleanup, library docs, and passing tests.
- 2026-07-18: Migrated package layout to `src/nfl/yahoo_fantasy` and revalidated tests.
- 2026-07-18: Approved `fantasypros_fantasy` sublibrary plan and completed Milestone 1 contracts/validation scaffold.
