# Entity Standardization Blueprint

## Status
- State: S1-S7 Complete
- Last Updated: 2026-07-18
- Owner: GitHub Copilot + Project Maintainer

## Locked Decisions
1. Canonical source of truth for players, teams, and positions is nflverse data via nflreadpy.
2. Canonical players are sourced from `nflreadpy.load_players()`.
3. Canonical cross-source mappings should leverage `nflreadpy.load_ff_playerids()`.
4. Canonical team codes are sourced from `nflreadpy.load_schedules()`.
5. Canonical player identity is cross-season (single canonical id per player).
6. Historical team names map to current team identifiers (example: San Diego -> LAC).
7. High-confidence only for auto-matches; all lower-confidence candidates go to manual review queue tables.
8. Pipeline must not fail on unresolved entities.
9. Unresolved rows are persisted to rescued-records tables for later correction and replay.
10. Position taxonomy for v1 is fixed to: QB, RB, WR, TE, DST, K.
11. Position normalization must map `FB` and `HB` to `RB`.
12. Standardization outputs are required as both Python API returns and persisted tables.
13. Confidence thresholds are configurable by source and entity type.
14. Manual review decisions live in tables (no file-based review workflow in v1).
15. Queue workflows must be simple for end users to administer.

## Objective
Create a shared library component that standardizes player names, team names, and positions across providers (Yahoo, FantasyPros, future sources) against nflreadpy canonical data, with deterministic auto-matching and robust manual review/rescue workflows.

## Proposed Package
- `nfl.entity_standardization`

Submodules:
1. `nfl.entity_standardization.canonical`
2. `nfl.entity_standardization.normalize`
3. `nfl.entity_standardization.matching`
4. `nfl.entity_standardization.overrides`
5. `nfl.entity_standardization.pipeline`
6. `nfl.entity_standardization.storage`
7. `nfl.entity_standardization.validation`

## Canonical Data Contracts

### Canonical Players
- `canonical_player_id` (string, cross-season stable)
- `display_name`
- `first_name`
- `last_name`
- `current_team` (mapped to current franchise code)
- `primary_position` (QB/RB/WR/TE/DST/K)
- `aliases` (derived alias set)
- `source_version` (nflreadpy snapshot metadata)
- `cross_source_ids` (derived from `load_ff_playerids()` where available)

### Canonical Teams
- `canonical_team_id` (current franchise code, e.g. LAC)
- `canonical_team_name`
- `canonical_team_abbr`
- `aliases` (historical + alternate spellings; includes legacy names)
- `source_version`
- `team_code_authority`: `load_schedules()`

### Canonical Positions
- `canonical_position_id` and `canonical_position_code`
- Allowed codes: QB, RB, WR, TE, DST, K
- `aliases` (DEF -> DST, D/ST -> DST, PK -> K, FB -> RB, HB -> RB)

## Source Input Contract
For each inbound source record:
- `source_system` (yahoo, fantasypros, etc.)
- `source_entity_id` (nullable stable id)
- `raw_player_name`
- `raw_team_name`
- `raw_position`
- `season` (contextual only; canonical id remains cross-season)
- optional source-native metadata used as match evidence

## Output Contracts

### Standardized Entity Result
- `source_system`
- `source_entity_id`
- `canonical_player_id` (nullable)
- `canonical_team_id` (nullable)
- `canonical_position_code` (nullable)
- `standardized_player_name` (nullable)
- `standardized_team_name` (nullable)
- `standardized_position` (nullable)
- `player_confidence`
- `team_confidence`
- `position_confidence`
- `match_method_player` (exact, alias, fuzzy, override, unresolved)
- `match_method_team`
- `match_method_position`
- `explanation_json` (match rationale/evidence)
- `needs_review` (bool)
- `rescued` (bool)

### Queue Table (`std_match_queue`)
- One row per unresolved/low-confidence decision
- includes candidate list, scores, reason code, and first-seen timestamp
- user-admin fields:
  - `queue_status` (new, in_review, approved, rejected, deferred)
  - `assigned_to`
  - `priority` (high, medium, low)
  - `review_notes`
  - `resolved_at`
  - `resolved_by`
  - `resolution_action` (approve_candidate, manual_override, no_match)

### Queue Operations (Admin-Friendly)
- `std_match_queue_open`: convenience table/view-like projection for unresolved items (`queue_status in (new, in_review)`).
- `std_match_queue_history`: resolved decisions with full audit fields.
- `std_manual_overrides`: authoritative approved overrides consumed by matcher on next run.
- workflow rules:
  1. unresolved records are inserted as `queue_status=new`.
  2. approving a candidate writes/updates `std_manual_overrides` and marks queue row resolved.
  3. replay process picks up overrides and reprocesses corresponding rescued records.

### Rescued Records Table (`std_rescued_records`)
- Full original source payload plus unresolved fields
- replay status and resolution linkage after manual fix

### Mapping Table (`std_source_to_canonical_map`)
- Accepted mappings used for fast deterministic lookup on future runs
- includes validity window and provenance

## Matching Strategy

### Step 1: Deterministic Normalization
- Case folding, punctuation stripping, whitespace normalization
- suffix/initial harmonization
- team legacy alias normalization to current franchise code
- position alias normalization to QB/RB/WR/TE/DST/K, including FB/HB -> RB

### Step 2: Direct Match Layer
- source id lookup (if known in map table or discoverable via `load_ff_playerids()`)
- exact name match against canonical registry
- alias dictionary match

### Step 3: Constrained Fuzzy Match Layer
- candidates blocked by normalized team/position when available
- player similarity scoring across normalized full name + token forms
- tie-break rules based on:
  1. prior accepted mapping
  2. stronger team consistency
  3. stronger position consistency

### Step 4: Confidence Policy (Configurable)
- thresholds configurable per source and entity type
- auto-accept only above high threshold
- otherwise mark `needs_review=true`, write queue row, write rescued row
- pipeline continues without hard failure

## Public API

### Config
`StandardizationConfig`
- threshold configs by source and entity type
- per-source normalization toggles
- enable/disable fuzzy strategy by entity type
- queue/rescue persistence options

### Core Service
`EntityStandardizer`
- `standardize_record(record)`
- `standardize_batch(records)`
- `standardize_player_name(...)`
- `standardize_team_name(...)`
- `standardize_position(...)`

### Canonical Refresh
`CanonicalRegistryLoader`
- loads canonical players from `nflreadpy.load_players()`
- loads cross-source id mappings from `nflreadpy.load_ff_playerids()`
- loads canonical team codes from `nflreadpy.load_schedules()`
- derives canonical position alias map with FB/HB normalized to RB
- builds derived alias tables
- snapshots version metadata

## Storage Strategy (Polars + PyIceberg)
Persist the following tables via library persistence adapters:
1. `std_canonical_players`
2. `std_canonical_teams`
3. `std_canonical_positions`
4. `std_source_to_canonical_map`
5. `std_match_queue`
6. `std_rescued_records`
7. `std_standardized_outputs`

No Spark dependency required.

## Integration Points

### Yahoo Pipeline
- apply standardization after API extraction, before transform contract finalization
- persist both standardized outputs and unresolved queue/rescue entries

### FantasyPros Pipeline
- apply same shared standardizer on extracted player/team/position fields
- use mapping table to stabilize future runs where source ids drift

## Milestone Plan

### S1: Canonical Registry Foundation
- nflreadpy loaders for player/team/position canonical tables
- canonical contract validation

### S2: Normalization Engine
- deterministic normalization and alias expansion
- fixed position taxonomy mapping (QB, RB, WR, TE, DST, K)

### S3: Matching Engine
- direct + fuzzy match logic with confidence scoring
- source/entity configurable thresholds

### S4: Queue and Rescue Workflow
- write unresolved to queue and rescued tables
- replay hooks for post-review correction

### S5: Persistence and Public API
- Polars/PyIceberg persistence for all standardization artifacts
- stable public service API

### S6: Pipeline Integration
- integrate with `nfl.yahoo_fantasy` and `nfl.fantasypros_fantasy`
- add cross-pipeline regression tests

### S7: Operational Hardening
- metrics (auto-match rate, unresolved rate, override usage)
- deterministic replay validation and documentation

## Acceptance Criteria
1. Canonical players sourced from `nflreadpy.load_players()` and versioned in persisted artifacts.
2. `load_ff_playerids()` mappings are leveraged for cross-source identity resolution.
3. Team legacy names consistently resolve to current franchise identifiers using `load_schedules()` team codes.
4. Position outputs always in QB/RB/WR/TE/DST/K with FB/HB mapped to RB.
5. Low-confidence records never fail pipeline; they are queued and rescued.
6. Outputs available as both API returns and persisted tables.
7. Thresholds configurable by source and entity type.
8. Queue lifecycle can be managed entirely through review tables without editing files.

## Initial Defaults (Recommended)
- `auto_accept_threshold_player`: 0.97
- `auto_accept_threshold_team`: 0.995
- `auto_accept_threshold_position`: 1.0 for deterministic aliases, else queue
- `review_band_player`: [0.85, 0.97)
- all unresolved below review band are still rescued and queued

## Open Questions
- None currently blocking implementation.

## Progress Tracking

### Cadence
- Update this file after each completed milestone, and after any major scope/risk change.

### Progress Log

#### 2026-07-18 - S1 Completed (Canonical Registry Foundation)
- Summary:
  - Implemented canonical registry loader in `nfl.entity_standardization.canonical`.
  - Canonical players sourced from `nflreadpy.load_players()`.
  - Cross-source mappings sourced from `nflreadpy.load_ff_playerids()`.
  - Team code authority sourced from `nflreadpy.load_schedules()`.
- Decisions captured:
  - Cross-season player identity resolves to stable canonical player ids.

#### 2026-07-18 - S2 Completed (Normalization Engine)
- Summary:
  - Implemented deterministic normalization in `nfl.entity_standardization.normalize`.
  - Added team legacy normalization and fixed position taxonomy.
  - Added explicit `FB`/`HB` -> `RB` normalization.

#### 2026-07-18 - S3 Completed (Matching Engine)
- Summary:
  - Implemented exact/alias/fuzzy matching in `nfl.entity_standardization.matching`.
  - Added source-map-first and threshold-driven acceptance behavior.

#### 2026-07-18 - S4 Completed (Queue and Rescue Workflow)
- Summary:
  - Implemented queue/rescue generation and admin-friendly queue fields.
  - Implemented queue open/history table projections and manual override indexing.

#### 2026-07-18 - S5 Completed (Persistence and Public API)
- Summary:
  - Implemented public API via `EntityStandardizer`, `StandardizationConfig`, and `StandardizationResult`.
  - Implemented Polars persistence and dry-run Iceberg idempotency helpers for standardization tables.

#### 2026-07-18 - S6 Completed (Pipeline Integration)
- Summary:
  - Integrated optional standardization into `nfl.yahoo_fantasy.pipeline` and `nfl.fantasypros_fantasy.pipeline`.
  - Added standardization outputs into pipeline frames and return objects when enabled.

#### 2026-07-18 - S7 Completed (Operational Hardening)
- Summary:
  - Added validation contracts for canonical, mapping, queue, rescue, output, and manual override tables.
  - Added regression tests covering canonical loading, normalization, queue/rescue behavior, storage idempotency, and pipeline integration.

### Verification
- Test command: `C:/Users/EricTruett/miniconda3/envs/dbxconnect/python.exe -m pytest -q`
- Result: `40 passed`.
