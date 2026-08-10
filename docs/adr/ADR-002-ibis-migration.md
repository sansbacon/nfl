# ADR-002: Migrate Transform Layer to Ibis

**Status:** Accepted — Fully Implemented (v1.0.0 released)  
**Date:** 2025-07-29  
**Updated:** 2025-07-30  
**Deciders:** Project Maintainers  

## Context

The `nfl` library currently uses Polars as its sole DataFrame engine for transforms,
views, and validation. Storage adapters then persist Polars DataFrames to various
backends (local Parquet, DuckDB, PyIceberg, Unity Catalog via `nfl-databricks`).

This creates tight coupling: every transform function imports `polars`, every storage
adapter accepts `pl.DataFrame`, and switching execution engines (e.g., running transforms
inside DuckDB or PySpark) requires rewriting the entire pipeline.

[Ibis](https://ibis-project.org/) provides a single expression API that compiles to
15+ backends (DuckDB, Polars, PySpark, DataFusion, Snowflake, BigQuery, etc.). Adopting
Ibis would let us:

- Write transforms once, execute on any backend
- Eliminate per-backend storage adapters for read/transform/write flows
- Give end users backend choice via configuration (not code changes)
- Reduce the maintenance surface of the storage layer

## Decision

Adopt Ibis as the expression layer for transforms and views. Keep Polars for eager
extraction (API responses → DataFrames) and convert to Ibis at the transform boundary.
Use a hybrid approach for SCD2 mutations (Ibis for reads, backend-specific SQL for writes).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        End User Configuration                       │
│   PipelineConfigBase.backend = "duckdb" | "polars" | "pyspark" ...  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    nfl.common.backend                                │
│   get_backend(config) → ibis.BaseBackend                            │
│   (connection lifecycle, backend-specific init)                      │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
          ┌───────────┼───────────────┐
          │           │               │
          ▼           ▼               ▼
┌──────────────┐ ┌──────────┐ ┌────────────────┐
│  Extractors  │ │Transforms│ │    Storage      │
│ (eager)      │ │  (Ibis)  │ │ (Ibis → write)  │
│ Polars/dict  │ │          │ │                  │
│ → memtable   │ │ ibis.Table│ │ backend.create_ │
│              │ │ exprs    │ │ table / raw_sql  │
└──────────────┘ └──────────┘ └────────────────┘
```

---

## Backend Selection: How End Users Choose

### Config-Driven (Library Mode)

Extend `PipelineConfigBase` with a `backend` field:

```python
# nfl/common/config.py
from typing import Literal

BackendType = Literal["duckdb", "polars", "pyspark", "datafusion"]

@dataclass(frozen=True, slots=True)
class PipelineConfigBase:
    season: int = 2025
    backend: BackendType = "duckdb"            # NEW — replaces storage_target
    duckdb_path: str | Path = "./output/nfl.duckdb"
    pyspark_catalog: str = "nfl"               # NEW — for UC/PySpark
    pyspark_schema: str = "default"            # NEW
    dry_run: bool = True
    ingestion_date: date | None = None
```

The existing `StorageTarget` is deprecated but kept for backward compatibility
during the migration period (Phase 1–2). It maps to the new field:

| Old StorageTarget       | New BackendType | Notes                         |
| ----------------------- | --------------- | ----------------------------- |
| `"none"`                | `"duckdb"`      | In-memory, no persistence     |
| `"polars"`              | `"polars"`      | Ibis Polars backend + file IO |
| `"duckdb"`              | `"duckdb"`      | File-backed DuckDB            |
| `"unity_catalog"`       | `"pyspark"`     | PySpark + Delta/UC            |
| `"iceberg"`             | `"duckdb"`      | DuckDB + iceberg extension    |
| `"both"`                | `"pyspark"`     | Handled at persistence layer  |

### Backend Factory

```python
# nfl/common/backend.py
from __future__ import annotations

import ibis

from nfl.common.config import PipelineConfigBase


def get_backend(config: PipelineConfigBase) -> ibis.BaseBackend:
    """Resolve an Ibis backend connection from pipeline config."""
    match config.backend:
        case "duckdb":
            return ibis.duckdb.connect(str(config.duckdb_path))
        case "polars":
            return ibis.polars.connect()
        case "pyspark":
            # Assumes SparkSession is already active (Databricks runtime)
            return ibis.pyspark.connect(ibis.pyspark.Backend._session)
        case "datafusion":
            return ibis.datafusion.connect()
        case _:
            raise ValueError(f"Unsupported backend: {config.backend}")
```

### Notebook / Widget Mode (Databricks)

In consumer notebooks, the backend is chosen via a widget:

```python
dbutils.widgets.dropdown("backend", "pyspark", ["duckdb", "pyspark", "datafusion"])
config = PipelineConfig(backend=dbutils.widgets.get("backend"), ...)
backend = get_backend(config)
```

### Environment Variable Override

For CI and Docker:

```bash
export NFL_BACKEND=duckdb
export NFL_DUCKDB_PATH=:memory:
```

```python
import os
config = PipelineConfigBase(
    backend=os.getenv("NFL_BACKEND", "duckdb"),
    duckdb_path=os.getenv("NFL_DUCKDB_PATH", "./output/nfl.duckdb"),
)
```

---

## Migration Phases

### Phase 0: Add Ibis Dependencies

**Scope:** `pyproject.toml` only — no code changes.

```toml
[project.optional-dependencies]
ibis = [
    "ibis-framework[duckdb]>=9.0.0",
]
ibis-polars = [
    "ibis-framework[polars]>=9.0.0",
]
ibis-pyspark = [
    "ibis-framework[pyspark]>=9.0.0",
]
ibis-all = [
    "ibis-framework[duckdb,polars,pyspark,datafusion]>=9.0.0",
]
```

Keep `polars` and `pyarrow` as core deps — they remain the extraction format
and the zero-copy bridge to Ibis via `ibis.memtable(arrow_table)`.

**Deliverables:**
- [x] Updated `pyproject.toml` — added `ibis`, `ibis-polars`, `ibis-pyspark`, `ibis-all` extras
- [ ] CI matrix runs tests with `nfl[ibis]` installed
- [x] Smoke test: `import ibis; ibis.duckdb.connect(":memory:")` passes

---

### Phase 1: Backend Factory + Persistence Layer

**Scope:** New `nfl.common.backend` module; refactor `nfl.common.storage`.

**New modules:**
- `nfl/common/backend.py` — `get_backend()`, connection lifecycle
- `nfl/common/storage/ibis_writer.py` — unified write dispatcher

**Storage refactor:**

```python
# nfl/common/storage/ibis_writer.py
def persist_tables(
    tables: Mapping[str, ibis.Table],
    backend: ibis.BaseBackend,
    *,
    schema: str = "main",
    write_mode: Literal["overwrite", "append"] = "overwrite",
    dry_run: bool = False,
) -> list[WriteResult]:
    """Write Ibis table expressions to the active backend."""
    results = []
    for name, table in tables.items():
        fq_name = f"{schema}.{name}"
        if dry_run:
            results.append(WriteResult(name, fq_name, write_mode, table.count().execute(), 0))
            continue
        if write_mode == "overwrite":
            backend.create_table(fq_name, table, overwrite=True)
        elif write_mode == "append":
            backend.insert(fq_name, table)
        results.append(WriteResult(name, fq_name, write_mode, table.count().execute(), ...))
    return results
```

**Backward compatibility:**
- Existing `persist_with_polars`, `persist_to_duckdb`, `persist_to_iceberg` remain
  importable but emit `DeprecationWarning`.
- `nfl.common.storage.__init__` re-exports new `persist_tables` alongside legacy.

**Deliverables:**
- [x] `nfl.common.backend` module — `get_backend()`, `get_backend_from_env()` with DuckDB/Polars/PySpark/DataFusion
- [x] `nfl.common.storage.ibis_writer` — `persist_tables()`, `persist_from_polars()` with `_parse_table_name()` fix
- [x] Integration test: DuckDB `:memory:` round-trip (3 rows → persist → read back)
- [x] Deprecation warnings on legacy storage functions (noted in `__init__.py`)

---

### Phase 2: SCD2 Merge (Hybrid Approach)

**Scope:** Replace `nfl.common.storage.duckdb.merge_scd2` with a backend-aware version.

**Design decision:** SCD2 is inherently a mutation (UPDATE + INSERT). Ibis has no
MERGE primitive. We use the **hybrid** pattern:

1. Register source data as a temp table via `backend.create_table(..., temp=True)`
2. Use Ibis expressions for analysis (change detection, row counts)
3. Dispatch backend-specific MERGE SQL via `backend.raw_sql()`

```python
# nfl/common/storage/scd2.py
def merge_scd2_ibis(
    source: ibis.Table,
    target_name: str,
    natural_keys: tuple[str, ...],
    backend: ibis.BaseBackend,
    *,
    hash_column: str = "_record_hash",
) -> dict[str, int]:
    """SCD2 merge dispatched per backend."""
    # Register source as temp
    backend.create_table("_scd2_source", source, temp=True)

    # Dispatch mutation SQL
    match backend.name:
        case "duckdb":
            _scd2_duckdb(backend, target_name, natural_keys, hash_column)
        case "pyspark":
            _scd2_delta(backend, target_name, natural_keys, hash_column)
        case _:
            _scd2_relational_rebuild(backend, source, target_name, natural_keys, hash_column)

    backend.drop_table("_scd2_source")
```

For backends without MERGE (Polars, DataFusion), use the **full-table rebuild**
alternative: read target, compute diffs via anti-join + union, overwrite.

**Deliverables:**
- [x] `nfl.common.storage.scd2` module — `compute_record_hash()`, `merge_scd2()`
- [x] DuckDB MERGE path (`_scd2_duckdb` via `backend.raw_sql()`)
- [x] PySpark/Delta MERGE INTO path (`_scd2_delta`)
- [x] Relational rebuild fallback (`_scd2_relational_rebuild` — pure Ibis anti-join + union)
- [x] `compute_record_hash` ported to Ibis (concat + hash)
- [x] Unit tests with DuckDB `:memory:` — bootstrap 3 rows, update 2 (expire/insert verified)

---

### Phase 3: Migrate Transforms

**Scope:** Convert `transforms.py` in each source module from Polars to Ibis.

**Pattern (before):**
```python
def _coerce_frame_types(frame: pl.DataFrame) -> pl.DataFrame:
    casts = []
    for col in frame.columns:
        if col in _INT_COLUMNS:
            casts.append(pl.col(col).cast(pl.Int64, strict=False))
    return frame.with_columns(casts) if casts else frame
```

**Pattern (after):**
```python
def _coerce_types(table: ibis.Table) -> ibis.Table:
    casts = {}
    for col in table.columns:
        if col in _INT_COLUMNS:
            casts[col] = table[col].try_cast("int64")
        elif col in _FLOAT_COLUMNS:
            casts[col] = table[col].try_cast("float64")
    return table.mutate(**casts) if casts else table
```

**Key mappings:**

| Polars                          | Ibis equivalent                       |
| ------------------------------- | ------------------------------------- |
| `pl.col(x).cast(pl.Int64)`      | `table[x].try_cast("int64")`          |
| `frame.with_columns([...])`     | `table.mutate(...)`                   |
| `frame.select([...])`           | `table.select(...)`                   |
| `frame.filter(pl.col(x) > 5)`   | `table.filter(table.x > 5)`           |
| `frame.join(other, on=...)`     | `table.join(other, predicates=...)`   |
| `frame.sort([...])`             | `table.order_by(...)`                 |
| `frame.group_by(...).agg(...)`  | `table.group_by(...).aggregate(...)`  |
| `frame.explode("col")`          | `table.unnest("col")`                 |
| `pl.col(x).rank().over([...])`  | `table[x].rank().over(ibis.window(group_by=[...]))` |
| `pl.struct([...]).rank()`       | Requires row_number() or dense_rank() with order_by |
| `frame.height`                  | `table.count().execute()`             |
| `frame.is_empty()`              | `table.count().execute() == 0`        |

**Ibis gaps requiring workarounds:**

1. **`pl.struct([...]).rank()`** (used in `views.py` for position_pick):
   → Use `ibis.dense_rank().over(ibis.window(group_by=[...], order_by=[...]))`

2. **`frame.explode("stats")`** on struct-list columns:
   → `table.unnest("stats")` if the column is an array of structs.
   → May need `table.select(ibis.unnest(table.stats))` depending on schema.

3. **Empty DataFrame construction** (contract stubs):
   → `ibis.table(schema, name="empty")` or `ibis.memtable(pa.table(schema))`

**Migration order (by complexity, ascending):**
1. `nfl.fantasypros_fantasy.transforms` — simplest (flat records, no explode)
2. `nfl.entity_standardization` — row-level matching (partially stays in Python)
3. `nfl.yahoo_fantasy.transforms` — struct explode, more complex casts
4. `nfl.yahoo_fantasy.views` — window functions, multi-table joins
5. `nfl.sleeper_fantasy`, `nfl.espn_fantasy`, `nfl.nflverse_fantasy` — TBD

**TransformResult changes:**
```python
@dataclass(frozen=True, slots=True)
class TransformResult:
    tables: dict[str, ibis.Table]  # was: dict[str, pl.DataFrame]
```

**Deliverables:**
- [x] FantasyPros `transforms_ibis.py` — `transform_entity()`, `transform_nfl()`, `transform()`
- [x] Yahoo `transforms_ibis.py` — NFL + NBA transforms, expanded type sets
- [x] Yahoo `views_ibis.py` — `_build_vw_draft_results` (window ranks), `_build_v_player_fantasy_scoring` (multi-join + unnest)
- [x] Entity standardization `ibis_adapter.py` — `result_tables_to_ibis()`, `standardize_from_ibis()`, `standardize_from_ibis_to_ibis()`
- [x] Sleeper `transforms_ibis.py` — `players_to_dim_table()`, `players_to_adp_table()`
- [x] ESPN `transforms_ibis.py` — `players_to_ranks_table()`, season + weekly projection tables
- [x] NFLverse `transforms_ibis.py` — data-driven coercion (16 entities), string→boolean, date/datetime
- [x] Integration tests green on DuckDB `:memory:` (FantasyPros, NFLverse verified)

---

### Phase 4: Migrate Validation Contracts

**Scope:** Replace `validate_polars_frame` with Ibis schema inspection.

```python
def validate_ibis_table(
    table: ibis.Table,
    contract: EntityContract,
    *,
    allow_extra_columns: bool = True,
) -> None:
    """Validate an Ibis table against an EntityContract."""
    actual_cols = set(table.columns)
    missing = set(contract.required) - actual_cols
    if missing:
        raise ContractValidationError(
            f"Missing required columns for {contract.name}: {missing}"
        )
    if not allow_extra_columns:
        extra = actual_cols - contract.allowed_fields
        if extra:
            raise ContractValidationError(f"Unexpected columns: {extra}")
```

**Deliverables:**
- [ ] `validate_ibis_table` in `nfl.common.validation`
- [ ] EntityContract unchanged (already backend-agnostic)
- [ ] Per-source validation modules delegate to common validator

---

### Phase 5: Migrate Crosswalk + Matching

**Scope:** `nfl.common.crosswalk` currently uses PySpark directly. Migrate to Ibis.

```python
def load_canonical_crosswalk(backend: ibis.BaseBackend, catalog: str, schema: str) -> None:
    import nflreadpy as nflread
    ids_df = nflread.load_ff_playerids()
    ids_table = ibis.memtable(ids_df.to_arrow())
    fq_table = f"{catalog}.{schema}.dim_ff_player_ids"
    backend.create_table(fq_table, ids_table, overwrite=True)
```

**Note:** `nfl.common.matching.normalize_name` is pure Python string processing —
it does not need migration. It stays as-is and is applied pre-Ibis (during extraction)
or via a UDF if needed inside Ibis expressions.

**Deliverables:**
- [x] `load_crosswalk(backend, database=...)` — new Ibis interface (nflreadpy → Arrow → memtable → create_table)
- [x] `read_crosswalk(backend, database=...)` — read existing crosswalk table
- [x] Legacy `load_canonical_crosswalk(spark, ...)` kept with `DeprecationWarning`
- [x] `normalize_name` stays pure Python (no migration needed)
- [x] Tested with DuckDB `:memory:` — load, read, filter by ID verified

---

### Phase 6: Clean Up Legacy Adapters

**Scope:** Remove deprecated code paths after all sources are migrated.

- [x] **Deleted** `nfl.common.storage.polars`, `duckdb.py`, `iceberg.py`
- [x] **Deleted** per-source `storage/` directories (FantasyPros, Yahoo, Sleeper, NFLverse)
- [x] Removed `StorageTarget` literal, `resolve_backend()`, `storage_target`, `polars_output_dir`, `polars_file_format` from config
- [x] `storage/__init__.py` rewritten: Ibis-only exports (`persist_tables`, `compute_record_hash`, `merge_scd2`)
- [x] Legacy `pipeline.py` files replaced with deprecation stubs
- [x] All source `__init__.py` files cleaned of pipeline/storage re-exports
- [x] Removed `iceberg` optional dependency from `pyproject.toml`
- [x] `nfl-databricks` remains PySpark-native (no changes needed)
- [x] Version bumped to `nfl` 1.0.0

---

## Testing Strategy

| Layer           | Backend for Tests | Notes                            |
| --------------- | ----------------- | -------------------------------- |
| Unit tests      | DuckDB `:memory:` | Fast, no file IO                 |
| Integration     | DuckDB file       | Persistence, SCD2                |
| Databricks CI   | PySpark           | UC round-trip, Delta merge       |
| Local dev       | DuckDB file       | Default for `pytest`             |

**Fixture pattern:**
```python
@pytest.fixture(params=["duckdb", "polars"])
def backend(request, tmp_path):
    match request.param:
        case "duckdb":
            return ibis.duckdb.connect(str(tmp_path / "test.duckdb"))
        case "polars":
            return ibis.polars.connect()
```

---

## Risks and Mitigations

| Risk                                        | Mitigation                                       |
| ------------------------------------------- | ------------------------------------------------ |
| Ibis Polars backend less mature than DuckDB  | Default to DuckDB; Polars backend is optional    |
| `ibis.insert()` not stable on all backends  | Use `create_table(..., overwrite=True)` for now  |
| Window functions behave differently per BE   | Test each view on every supported backend        |
| PySpark backend performance overhead         | Only used in Databricks (cluster resources)      |
| Breaking change for downstream consumers    | Phased rollout with deprecation warnings         |
| `unnest`/explode semantics differ per BE     | Abstract behind a helper; test Yahoo views early |
| Entity standardization uses row-level Python | Keep matching in Python; only frame I/O uses Ibis|

---

## Design Decisions (Resolved)

| Question | Decision | Rationale |
| --- | --- | --- |
| **Polars backend** | Keep as a supported backend | Provides in-process option; some users prefer it |
| **Iceberg** | Drop local Iceberg support entirely | SQLite catalog was dev-only (ADR-001); not worth porting |
| **nfl-databricks** | Stays PySpark-native, not migrated | Interops via Arrow; Ibis migration scoped to `nfl` core |
| **Entity Standardization** | Keep fully in Python; convert I/O at boundaries | Row-level fuzzy matching doesn't benefit from Ibis |
| **Minimum Ibis version** | `>=9.0.0` | Needed for `backend.insert()` and `create_table` semantics |
| **ffdatwarehouse notebooks** | Out of scope (deprecated) | Library migration only |
| **Performance baseline** | No benchmark suite pre-migration | Unnecessary overhead |

---

## Open Questions

### Q1: PipelineRunResult Shape
`PipelineRunResult.frames` is currently `dict[str, pl.DataFrame]`. After migration:
- (a) Change to `dict[str, ibis.Table]` (lazy — forces `.execute()` at consumer)
- (b) Change to `dict[str, pa.Table]` (materialized Arrow — universal interchange)
- (c) Keep `dict[str, pl.DataFrame]` and materialize at the boundary

**Recommendation:** Option (b) — `pa.Table` is the universal zero-copy interchange
format. Consumers can trivially convert: `pl.from_arrow(t)`, `ibis.memtable(t)`,
or `spark.createDataFrame(t)`. It avoids forcing a Polars dependency on downstream
consumers and avoids the lazy-execution footgun of returning unevaluated Ibis exprs.

---

## Timeline Estimate

| Phase | Effort (days) | Depends On   |
| ----- | ------------- | ------------ |
| 0     | 1             | —            |
| 1     | 3–4           | Phase 0      |
| 2     | 3–4           | Phase 1      |
| 3     | 5–7           | Phase 1      |
| 4     | 1–2           | Phase 3      |
| 5     | 1–2           | Phase 1      |
| 6     | 2–3           | Phases 3–5   |
| **Total** | **16–23 days** |          |

Phases 2, 3, and 5 can run in parallel after Phase 1 is complete.

---

## Implementation Notes (Phases 0–4)

### New Files Created

| Module | File | Purpose |
| --- | --- | --- |
| `nfl.common` | `backend.py` | Backend factory (`get_backend`, `get_backend_from_env`) |
| `nfl.common` | `validation.py` | `EntityContract`, `validate_ibis_table`, `validate_primary_key` |
| `nfl.common.storage` | `ibis_writer.py` | `persist_tables`, `persist_from_polars`, `WriteResult` |
| `nfl.common.storage` | `scd2.py` | `compute_record_hash`, `merge_scd2` (DuckDB/Delta/rebuild) |
| `nfl.fantasypros_fantasy` | `transforms_ibis.py` | Full transform port (3 public functions) |
| `nfl.yahoo_fantasy` | `transforms_ibis.py` | NFL + NBA transforms |
| `nfl.yahoo_fantasy` | `views_ibis.py` | Draft results + fantasy scoring views |
| `nfl.sleeper_fantasy` | `transforms_ibis.py` | Dim players + ADP table wrappers |
| `nfl.espn_fantasy` | `transforms_ibis.py` | Ranks + projections (season/weekly) wrappers |
| `nfl.nflverse_fantasy` | `transforms_ibis.py` | Data-driven coercion (16 entities) |
| `nfl.entity_standardization` | `ibis_adapter.py` | I/O boundary adapter (in/out/round-trip) |

### Key Lessons Learned

1. **`ibis.cases()` API (v12.0.0):** Uses tuple syntax `ibis.cases((cond, val), ..., else_=default)` — the old chainable `.when().then().else_().end()` pattern was removed.

2. **Schema-qualified table names:** `backend.create_table("schema.table", ...)` creates a table literally named `"schema.table"` with a dot. Must use `backend.create_table(table_name, expr, database=schema)` with a parsed split.

3. **Architectural patterns by module complexity:**
   - **Simple (Sleeper/ESPN):** Dataclass → dict (row-level Python) + `ibis.memtable()` wrapper
   - **Medium (FantasyPros/Yahoo transforms):** Contract validation + type coercion + `ibis.memtable(data)`
   - **Complex (NFLverse):** Data-driven `DATASET_COERCIONS` dict with string→boolean via `ibis.cases()`
   - **Boundary-only (Entity Standardization):** Core stays Python; adapter converts at I/O seams
   - **Advanced (Yahoo views):** `ibis.dense_rank().over()`, multi-table joins, unnest

4. **Ibis `dense_rank()` is 0-based** (SQL standard); add `+ 1` to match Polars 1-based ranks.

### Completed (1.0.0 Release)

- [x] Phase 5: Migrate `nfl.common.crosswalk` — `load_crosswalk()`, `read_crosswalk()` + deprecation
- [x] Phase 6: Deprecate legacy storage adapters, remove `StorageTarget`, clean `PipelineConfigBase`
- [x] Delete deprecated files: `polars.py`, `duckdb.py`, `iceberg.py`, all per-source `storage/` directories
- [x] Remove `iceberg` optional dependency from `pyproject.toml`
- [x] Replace legacy `pipeline.py` orchestrators with deprecation stubs (FantasyPros, Yahoo, ESPN, NFLverse)
- [x] Clean `__init__.py` re-exports across all source modules
- [x] Bump version to `nfl` 1.0.0
- [x] Final verification: 70 .py files parse, all imports clean, no legacy references remain

### Remaining Work (Post-1.0.0)

- [x] CI: Add `nfl[ibis]` to test matrix (`ci.yml` → `--extra ibis`, `ibis-framework[duckdb]` in dev deps)
- [x] Formal pytest suite: `test_ibis_common.py` (9 tests) + `test_ibis_transforms.py` (7 tests) — 16 total, all passing
- [x] Port `yahoo_fantasy/historical_auction.py` — storage import already cleaned; parses OK
- [ ] Rewrite pipeline orchestrators on Ibis (currently deprecation stubs)

---

## References

- [Ibis documentation](https://ibis-project.org/docs/)
- [Ibis backend matrix](https://ibis-project.org/support_matrix)
- [ADR-001: PyIceberg Catalog](./ADR-001-pyiceberg-catalog.md)
- Ibis GitHub: `ibis-project/ibis` (MIT licensed)
