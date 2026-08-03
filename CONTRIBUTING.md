# Contributing to `nfl`

## Quick Start

```bash
# Clone and install
git clone <repo-url> && cd nfl
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run tests (excludes integration tests by default)
pytest

# Run only unit tests explicitly
pytest -m "not integration"

# Run with coverage
pytest --cov --cov-report=term-missing

# Lint / format
ruff check src/ tests/
ruff format src/ tests/
```

## Project Layout

```
src/nfl/
├── common/              # Shared utilities (crosswalk, matching, storage)
│   ├── crosswalk.py     # load_canonical_crosswalk()
│   ├── matching.py      # normalize_name()
│   └── storage/         # Canonical persistence layer
│       ├── polars.py    # persist_with_polars()
│       ├── unity_catalog.py  # UCTableConfig, persist_to_uc_tables()
│       └── iceberg.py   # IcebergCatalogConfig, persist_to_iceberg()
├── yahoo_fantasy/       # Yahoo Fantasy (full module)
├── fantasypros_fantasy/ # FantasyPros
├── nflverse_fantasy/    # NFLverse
├── sleeper_fantasy/     # Sleeper (public API)
├── espn_fantasy/        # ESPN
└── entity_standardization/  # Cross-source entity resolution

tests/                   # pytest test suite
examples/                # Databricks notebooks (load, match, query)
scripts/                 # CLI tools (load_data, rebuild_catalog)
blueprints/              # Architecture & design docs
```

## Adding a New Source

Follow the schema-per-source convention (`nfl.<prefix>`):

### 1. Create the module directory

```
src/nfl/<source>_fantasy/
├── __init__.py      # Public exports + __all__
├── api.py           # Client + data models
├── transforms.py    # Raw → dim/fact row builders
├── matching.py      # Crosswalk matching (name+position)
├── pipeline.py      # PipelineConfig, run_pipeline()
└── storage/
    ├── __init__.py
    └── unity_catalog.py  # Thin config wrapper → delegates to common
```

### 2. Implement the module

| File | Key pattern |
|------|-------------|
| `api.py` | Dataclass models, HTTP client, error types |
| `transforms.py` | Pure functions: `players_to_dim_rows()`, `*_to_fact_rows()` |
| `matching.py` | Use `nfl.common.matching.normalize_name` + `dim_ff_player_ids` crosswalk join |
| `storage/unity_catalog.py` | `SourceUCTableConfig` → delegates to `nfl.common.storage.persist_to_uc_tables()` |
| `pipeline.py` | `PipelineConfig` (season, storage_target, dry_run) + `run_pipeline()` |

### 3. Table naming conventions

* Schema: `nfl.<2-letter-prefix>` (e.g., `nfl.sl` for Sleeper)
* Dimension tables: `dim_<prefix>_<entity>` (e.g., `dim_sl_players`)
* Fact tables: `fact_<prefix>_<entity>` (e.g., `fact_sl_adp`)
* Player map: `<prefix>_player_map` (e.g., `sl_player_map`)
* Current view: `vw_current_<prefix>_<entity>`

### 4. SCD2 conventions for fact tables

* Natural key columns: `(season, <source>_player_id)` minimum
* Required SCD2 columns: `ingestion_date DATE`, `end_date DATE`, `is_current BOOLEAN`
* MERGE pattern: expire changed rows (set `is_current=false`, `end_date=today`), then insert new

### 5. Matching to crosswalk

The canonical crosswalk is `nfl.common.dim_ff_player_ids` (loaded from `nflreadpy`).
`mfl_id` is the universal primary key.

* If the source has a known ID column in the crosswalk (e.g., `espn_id`, `yahoo_id`), use a direct join first
* Fallback: `normalize_name()` + position matching
* Fuzzy fallback: last name + first-3-chars + position
* Persist to `<prefix>_player_map` (source_id → mfl_id, match_method)

### 6. Add tests

* `tests/test_<source>_transforms.py` — pure unit tests (no mocking needed)
* `tests/test_<source>_pipeline.py` — integration with `@patch` on the API client
* Mark Spark/external-API tests with `@pytest.mark.integration`

### 7. Create a notebook

* `examples/load_<source>_data_uc` — widget parameterized (CATALOG, SCHEMA, SEASON)
* Follow the pattern: fetch → transform → create schema/tables → MERGE → create view → gap check

### 8. Update exports

* Add to `src/nfl/<source>_fantasy/__init__.py`
* Add submodule to `src/nfl/__init__.py` → `__all__`

## Testing Guidelines

* All `assert` statements must include an error message showing variable values
  (e.g., `assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"`)
* Use `pytest.mark.integration` for tests that require Spark, network, or UC access
* Mock external HTTP calls — never hit real APIs in CI
* Test the transform layer independently from the API layer

## Code Style

* **Formatter**: ruff format (line-length 100)
* **Linter**: ruff (rules: E, F, I, B, UP, SIM, RUF)
* **Type hints**: encouraged but not enforced (mypy runs in CI with `--ignore-missing-imports`)
* **Imports**: isort via ruff (first-party = `nfl`)
* **Docstrings**: NumPy style for public functions
* No `black` — ruff-format is the single formatter

## Commit Messages

Follow conventional commits:

* `feat:` — new feature or module
* `fix:` — bug fix
* `refactor:` — code restructuring without behavior change
* `chore:` — tooling, CI, deps
* `docs:` — documentation only
* `test:` — adding or fixing tests
