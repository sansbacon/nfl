# Entity Standardization API Reference

The `nfl.entity_standardization` module provides cross-source entity matching and canonical player/team resolution. It accepts records from any source pipeline and produces a unified set of canonical identifiers, match decisions, and operational review queues.

## Quick Import

```python
from nfl.entity_standardization import (
    EntityStandardizer,
    StandardizationConfig,
    StandardizationResult,
    CanonicalRegistry,
    CanonicalRegistryLoader,
)
```

---

## Standardizer

### `EntityStandardizer`

Main class for batch standardization of player, team, and position records.

```python
standardizer = EntityStandardizer(
    config=StandardizationConfig(),
    registry=CanonicalRegistry(),
)
result = standardizer.standardize_batch(records)
```

**Constructor parameters:**

| Parameter | Type | Description |
|---|---|---|
| `config` | `StandardizationConfig` | Matching thresholds and persistence options |
| `registry` | `CanonicalRegistry` | Canonical entity registry |

### `standardize_batch`

```python
standardize_batch(records: list[dict]) -> StandardizationResult
```

Processes a list of source records. Each record must include identifying fields (e.g. `player_name`, `team`, `position`).

Returns a `StandardizationResult` containing:

| Field | Type | Description |
|---|---|---|
| `standardized` | `pl.DataFrame` | Records with canonical IDs attached |
| `source_to_canonical_map` | `pl.DataFrame` | Source ID → canonical ID mapping |
| `match_queue` | `pl.DataFrame` | Low-confidence matches queued for review |
| `rescued_records` | `pl.DataFrame` | Unresolved records staged for replay |
| `manual_overrides_applied` | `int` | Count of manual overrides applied |

---

## Configuration

### `StandardizationConfig`

| Field | Type | Default | Description |
|---|---|---|---|
| `player_threshold` | `float` | `0.97` | Minimum fuzzy score for auto-accept (players) |
| `team_threshold` | `float` | `0.995` | Minimum fuzzy score for auto-accept (teams) |
| `position_threshold` | `float` | `1.0` | Minimum score for auto-accept (positions) |
| `persist_tables` | `bool` | `False` | Write operational tables to storage |
| `iceberg_enabled` | `bool` | `False` | Use Iceberg for operational table persistence |
| `iceberg_dry_run` | `bool` | `True` | Dry-run mode for Iceberg writes |

**Threshold guidance:**

- Start with defaults; lower `player_threshold` to `0.90`–`0.95` to auto-accept more fuzzy matches.
- Use the match queue to review and escalate low-confidence records.
- Apply manual overrides to permanently resolve recurring edge cases.

---

## Registry

### `CanonicalRegistry`

In-memory store of canonical players, teams, and positions. Used by the standardizer for lookup and matching.

```python
registry = CanonicalRegistry()
```

### `CanonicalRegistryLoader`

Loads a `CanonicalRegistry` from persisted storage (Iceberg or local Parquet files).

```python
loader = CanonicalRegistryLoader(iceberg_catalog=catalog)
registry = loader.load()
```

---

## Supporting Modules

### `canonical`

Defines canonical entity data classes:

- `CanonicalPlayer` — normalized player identity.
- `CanonicalTeam` — normalized team identity.
- `CanonicalPosition` — normalized position identity.

### `matching`

Low-level name normalization and fuzzy matching utilities:

```python
from nfl.entity_standardization.matching import normalize_name, fuzzy_match_score

score = fuzzy_match_score("Patrick Mahomes", "Pat Mahomes")
```

### `overrides`

Manual override management:

```python
from nfl.entity_standardization.overrides import load_overrides, apply_overrides
```

### `normalize`

Text normalization utilities for names, teams, and positions:

```python
from nfl.entity_standardization.normalize import normalize_player_name, normalize_team_abbr
```

---

## Operational Tables

When `persist_tables=True`, the standardizer writes these tables:

| Table | Description |
|---|---|
| `std_standardized_outputs` | Normalized record-level outcomes |
| `std_source_to_canonical_map` | Source ID → canonical player mapping |
| `std_match_queue` | All unresolved or low-confidence rows |
| `std_match_queue_open` | Active review queue (`new`, `in_review` status) |
| `std_match_queue_history` | Resolved review history |
| `std_rescued_records` | Unresolved payloads staged for replay |
| `std_manual_overrides` | Human-approved corrections |
| `std_canonical_players` | Canonical player dimension |
| `std_canonical_teams` | Canonical team dimension |
| `std_canonical_positions` | Canonical position dimension |

---

## Usage Patterns

### Attach standardization to Yahoo Fantasy pipeline

```python
from nfl.yahoo_fantasy import PipelineConfig, run_pipeline
from nfl.entity_standardization import StandardizationConfig

config = PipelineConfig(
    storage_target="polars",
    standardization_enabled=True,
    standardization_config=StandardizationConfig(
        player_threshold=0.95,
        persist_tables=True,
    ),
)
result = run_pipeline(league_key="461.l.717896", sport="nfl", oauth_session=oauth, config=config)
```

### Standalone batch standardization

```python
from nfl.entity_standardization import EntityStandardizer, StandardizationConfig, CanonicalRegistry

standardizer = EntityStandardizer(
    config=StandardizationConfig(player_threshold=0.95),
    registry=CanonicalRegistry(),
)

records = [
    {"source": "yahoo", "player_name": "Patrick Mahomes", "team": "KC", "position": "QB"},
    {"source": "fp",    "player_name": "Pat Mahomes",     "team": "KCC", "position": "QB"},
]

result = standardizer.standardize_batch(records)
print(result.standardized)
print(result.match_queue)
```
