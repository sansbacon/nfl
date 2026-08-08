# ADR-001: PyIceberg as the Iceberg Catalog Access Layer

| Field       | Value                          |
|-------------|--------------------------------|
| **Status**  | Accepted (with conditions)     |
| **Date**    | 2026-08-08                     |
| **Authors** | Project Maintainer, Copilot    |
| **Issue**   | [#17](https://github.com/sansbacon/nfl/issues/17) |

---

## Context

The `nfl` package ingests data from multiple fantasy football sources (Yahoo, FantasyPros, ESPN, Sleeper, NFLverse) and persists normalized Polars DataFrames to Apache Iceberg tables.  The maintainer uses Unity Catalog on Databricks for personal use, but wants a catalog option available to users who do not have Databricks access.

This ADR evaluates whether [PyIceberg](https://py.iceberg.apache.org/) is the right library to fill that role, or whether a different approach would better serve the project's size, audience, and goals.

---

## Decision Drivers

1. **Accessibility** – The catalog option must be usable without paid cloud services.
2. **Simplicity** – A library of this scope should not impose a complex operational burden on contributors or users.
3. **Polars compatibility** – The project writes `pl.DataFrame` outputs. The catalog layer must accept Arrow-compatible inputs without a heavy translation layer.
4. **Open-table-format interoperability** – Data should be readable by common data warehouse tools (Spark, Trino, DuckDB, Databricks, BigQuery Omni, etc.).
5. **Maintenance surface** – The maintainer works alone; dependencies that require ongoing operational expertise are a liability.
6. **Unity Catalog parity** – The OSS path should produce artifacts that Unity Catalog users can also consume.

---

## Options Considered

### Option A – PyIceberg with a local SQLite catalog (current approach)

Write Polars DataFrames to Iceberg tables using `pyiceberg`, backed by a local SQLite catalog (`iceberg_catalog.db`) and a local `./warehouse` directory of Parquet data files.

### Option B – DuckDB + Parquet files (no Iceberg)

Persist outputs as Parquet files named by entity, and expose them via DuckDB for ad-hoc querying.  No Iceberg catalog.

### Option C – Delta Lake via `deltalake` (python-delta-lake)

Use Delta Lake format with the `deltalake` Python package as the open-table alternative.

### Option D – PyIceberg with a REST catalog (Lakeformation / Polaris / Gravitino)

Same as Option A but backed by a REST catalog endpoint instead of SQLite. Requires running a separate catalog service.

---

## Detailed Analysis

### Option A – PyIceberg + SQLite catalog

**What it does well**

- `pyiceberg` supports a [SQLite catalog backend](https://py.iceberg.apache.org/configuration/#sqlite-catalog) with zero server infrastructure: just a local `.db` file and a warehouse directory.
- Produces valid Apache Iceberg tables that any Iceberg-aware reader (DuckDB, Spark, Trino) can consume later, including Unity Catalog if the warehouse is stored on cloud object storage.
- The `polars` → `pyarrow` → Iceberg path is one API call (`tbl.append(frame.to_arrow())`), which is already implemented in `src/nfl/common/storage/iceberg.py`.
- Iceberg's metadata layer handles schema evolution, partition spec changes, and time-travel without the application having to manage those concerns.

**Risks and reasons NOT to adopt PyIceberg**

1. **Installation weight.** `pyiceberg>=0.7` pulls in `pyarrow`, `pydantic`, `tenacity`, `pyparsing`, and optional JVM bridges. For a pure-analytics library, this is a non-trivial transitive dependency graph that can surprise users who just want the scraping / normalization layer.

2. **SQLite catalog is not production-grade.** The SQLite backend is officially described as useful for *local development and testing*. It does not support concurrent writes and has no replication.  Users who try to build a real shared warehouse on it will hit limitations quickly.

3. **Catalog portability gap.** Metadata written to a local SQLite catalog cannot be moved to Unity Catalog or another REST catalog without re-ingestion. The two backends are not compatible at the metadata level, so the "easy migration" story is weaker than it first appears.

4. **Complexity mismatch.** Most users of this library want a clean DataFrame in memory. Adding a full Iceberg catalog layer for local persistence is architecturally heavier than the problem demands for many use cases.

5. **Iceberg Python API surface is still maturing.** Breaking changes between minor versions (`0.6 → 0.7`) have required downstream fixes (e.g., `pyiceberg` DeprecationWarnings already suppressed in `pyproject.toml`). This is ongoing maintenance work.

6. **Dry-run semantics are custom, not standard.** The current `persist_to_iceberg()` function implements a bespoke idempotency store in a JSON file (`.iceberg/write_log.json`). This is not a feature of PyIceberg itself and adds a layer of state that can get out of sync.

### Option B – DuckDB + Parquet files

**Advantages**

- Near-zero overhead: `frame.write_parquet(path)` is one line.
- DuckDB can query a directory of Parquet files with full SQL support.
- No catalog daemon, no metadata store, no dependency beyond `polars` (which the project already requires).
- Many analysts are already familiar with the DuckDB + Parquet workflow.
- A folder of Parquet files is the simplest possible artifact to hand off to another tool.

**Disadvantages**

- No open-table-format metadata (no schema history, no time-travel, no partition pruning via Iceberg manifests).
- Users who want to register data in Unity Catalog or Polaris must re-ingest from Parquet, which is easy but manual.
- File naming / partitioning conventions must be managed by the application.

### Option C – Delta Lake via `deltalake`

**Advantages**

- `python-delta-lake` (the Rust-backed library) is lightweight and writes Delta Lake transaction logs without a JVM.
- Delta Lake is broadly supported (Databricks, Synapse, BigQuery, Athena via manifests).
- Schema enforcement and ACID writes at the file level.

**Disadvantages**

- Delta Lake is less universally adopted in the open-source community than Iceberg. Trino and Hive support exists but is less mature.
- Adds another major dependency with its own version cadence.
- Less alignment with the Unity Catalog path (Unity Catalog supports both Iceberg and Delta, but the maintainer is already working in Iceberg there).

### Option D – PyIceberg with a REST catalog

**Advantages**

- Uses the same `pyiceberg` API as Option A but backed by a proper catalog service (Apache Gravitino, Project Nessie, Polaris, AWS Glue REST).
- Enables true catalog portability and concurrent access.

**Disadvantages**

- Requires running or subscribing to a catalog service, which contradicts the accessibility driver.
- Much higher operational complexity for a community library.

---

## Tradeoffs Summary

| Criterion               | Option A (PyIceberg/SQLite) | Option B (DuckDB/Parquet) | Option C (Delta Lake) |
|-------------------------|-----------------------------|---------------------------|------------------------|
| Zero-infra setup        | ✅ (SQLite only)             | ✅                         | ✅                     |
| Polars integration      | ✅ (via Arrow)               | ✅ (native)                | ✅ (via Arrow)         |
| Iceberg compatibility   | ✅                           | ❌                         | ❌                     |
| Unity Catalog parity    | ⚠️ (metadata gap)           | ⚠️ (re-ingest required)   | ⚠️ (supported but ≠ Iceberg) |
| Dep footprint           | ⚠️ heavy                    | ✅ minimal                 | ⚠️ moderate            |
| Production catalog      | ❌ (SQLite limits)           | ❌                         | ⚠️ (file-level only)  |
| Schema evolution / TT   | ✅                           | ❌                         | ✅                     |
| Operational complexity  | Low (SQLite)                | Very low                  | Low                    |
| Maintenance risk        | Medium (API churn)          | Low                       | Low                    |

---

## Decision

**Retain PyIceberg (Option A) as the default OSS catalog path, subject to the following conditions:**

1. **PyIceberg remains an optional dependency.** The core data-extraction and normalization modules (`yahoo_fantasy`, `fantasypros_fantasy`, etc.) must be importable and fully functional without `pyiceberg` installed. Storage adapters are already separate modules; `pyiceberg` should be moved to an `[iceberg]` optional extra so that users who only want the scraping / Polars layer are not forced to install it.

2. **The SQLite catalog is explicitly scoped to local development and single-user warehouse use.** Documentation must state that the SQLite catalog is not suitable for concurrent access or production multi-user environments.

3. **A Parquet-only path (Option B semantics) must be offered as the lowest-friction alternative.** Many users want `pl.DataFrame` outputs they can consume immediately. A simple `write_parquet` utility that requires no catalog setup should be the default when no catalog is configured.

4. **Deprecate the bespoke JSON idempotency store.** The `.iceberg/write_log.json` file is a maintenance liability. Idempotency at the PyIceberg layer should be handled by Iceberg's own snapshot semantics where possible, or removed in favour of letting callers control re-runs.

5. **Monitor PyIceberg's REST catalog support.** When `pyiceberg` REST catalog reaches stable status and free-tier REST catalog services (e.g., Polaris OSS, Gravitino) are readily deployable via Docker, this ADR should be revisited to promote REST catalog to the default backend.

---

## Success Criteria

- A user can install `nfl` (core) without `pyiceberg` and get normalized DataFrames.
- A user can install `nfl[iceberg]` and persist DataFrames to a local Iceberg warehouse with a single function call and no additional infrastructure.
- The same Parquet files in `./warehouse` are readable by DuckDB (`read_parquet`), Spark, and Unity Catalog external tables without re-ingestion.
- Zero new DeprecationWarnings from `pyiceberg` after a dependency bump.
- The idempotency mechanism does not require managing a separate `.iceberg/write_log.json` file outside of normal Iceberg operations.

---

## Exit Strategy

If PyIceberg adoption fails (e.g., API instability makes upgrades too costly, or user feedback shows the dependency weight is a barrier), the exit path is:

1. **Emit Parquet files** to `./warehouse/<namespace>/<entity>/` with a consistent naming convention that Unity Catalog can register as external tables.
2. **Drop the `pyiceberg` dependency** from `pyproject.toml`.
3. **Provide a one-time migration script** that re-registers existing SQLite-catalog tables as Unity Catalog external Iceberg tables using the Databricks CLI.

Because the current storage layer already separates PyIceberg behind thin adapters (`src/nfl/common/storage/iceberg.py`), replacing the backend with a plain Parquet writer requires changes in only those adapter files and the `pyproject.toml`, not in any pipeline or transformation code.

---

## References

- [PyIceberg documentation](https://py.iceberg.apache.org/)
- [PyIceberg SQLite catalog](https://py.iceberg.apache.org/configuration/#sqlite-catalog)
- [Apache Iceberg specification](https://iceberg.apache.org/spec/)
- [DuckDB Iceberg extension](https://duckdb.org/docs/extensions/iceberg)
- [Unity Catalog open-source](https://www.unitycatalog.io/)
- [Delta Lake Python bindings](https://delta-io.github.io/delta-rs/)
