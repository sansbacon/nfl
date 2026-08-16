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
│   └── storage/         # Platform-agnostic persistence
│       ├── polars.py    # persist_with_polars()
│       └── iceberg.py   # IcebergCatalogConfig, persist_to_iceberg()
├── yahoo_fantasy/       # Yahoo Fantasy (full module)
├── fantasypros_fantasy/ # FantasyPros
├── nflverse_fantasy/    # NFLverse
├── sleeper_fantasy/     # Sleeper (public API)
├── espn_fantasy/        # ESPN
├── fantasylife_fantasy/  # Fantasy Life (CSV/HTML)
├── fantasypoints_fantasy/ # Fantasy Points (CSV, redraft PPR)
└── entity_standardization/  # Cross-source entity resolution

tests/                   # pytest test suite
examples/                # Databricks notebooks (load, match, query)
scripts/                 # CLI tools (load_data, rebuild_catalog)
blueprints/              # Architecture & design docs
```

> **Databricks / Unity Catalog support** lives in the separate
> [`nfl-databricks`](../nfl-databricks/) package (`pip install nfl[databricks]`).
> That package provides `UCTableConfig`, `persist_to_uc_tables()`, and the
> Lakeflow Connect community connector. Do **not** add PySpark or
> Databricks-specific code to this repo.

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
    ├── polars.py    # Local file persistence
    └── iceberg.py   # PyIceberg persistence (optional)
```

### 2. Implement the module

| File | Key pattern |
|------|-------------|
| `api.py` | Dataclass models, HTTP client, error types |
| `transforms.py` | Pure functions: `players_to_dim_rows()`, `*_to_fact_rows()` |
| `matching.py` | Use `nfl.common.matching.normalize_name` + `dim_ff_player_ids` crosswalk join |
| `storage/polars.py` | Thin wrapper → delegates to `nfl.common.storage.persist_with_polars()` |
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

### 7. Manual Upload Sources (Subscription / No-API)

For sources that have no public API (e.g. ETR, Fantasy Life, Fantasy Points), use a Volume-based
incoming/processed pattern instead of live scraping:

```
/Volumes/nfl/<source>/<source>_volume/incoming/<feed_name>/   -- drop new exports here
/Volumes/nfl/<source>/<source>_volume/processed/<feed_name>/  -- archived after successful load
```

**Loader notebook conventions:**

* Expose the incoming/processed paths as **widgets** (`SOURCE_PATH`, `ARCHIVE_PATH`) —
  never hardcode a path so the drop location can be changed without editing code.
* Move a file to `processed/` **only after** a successful MERGE, so re-running the notebook
  never double-loads a file.
* Widget validation pattern (same as other notebooks):
  ```python
  assert all((CATALOG, SCHEMA, SEASON, SOURCE_PATH, ARCHIVE_PATH)), \
      f'ERROR: {CATALOG=} {SCHEMA=} {SEASON=} {SOURCE_PATH=} {ARCHIVE_PATH=} must be set'
  ```
* Use `dbutils.fs.mv()` (not `cp` + `rm`) for atomic archive operations.
* If the source publishes multiple feed types (e.g. ETR has `ranks/` today and
  `projections/` in the future), give each its own subfolder under `incoming/` and
  `processed/` rather than mixing file types in one directory.

### 8. Create a notebook

* `examples/load_<source>_data_uc` — widget parameterized (CATALOG, SCHEMA, SEASON)
* Follow the pattern: fetch → transform → create schema/tables → MERGE → create view → gap check

### 9. Update exports

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

## Known Issues / Workarounds

### Yahoo Fantasy OAuth app authorization broken (found 2026-08-13)

The registered Yahoo Developer app (`dbxconnect`, credentials in `.secrets/credentials.json`) returns
`403 "This application is not authorized to perform this action"` on **every** `fantasysports.yahooapis.com`
endpoint (games discovery, league metadata, player pool), even with:

* A freshly refreshed OAuth token (ruled out expiry)
* A brand-new full re-consent flow after fixing a `redirect_uri` mismatch (ruled out stale scope)
* "Fantasy Sports" Read permission confirmed enabled on the app

This points to an app-verification/platform-level restriction on Yahoo's side, not fixable via
credentials or token changes. Needs escalation with Yahoo directly or recreating the app.

**Workaround — public draft analysis endpoint (no OAuth needed):** The public
`https://football.fantasysports.yahoo.com/f1/draftanalysis` page renders its table client-side by calling
Yahoo's **public read-only** API host directly, which requires **no OAuth token**:

```
https://pub-api-ro.fantasysports.yahoo.com/fantasy/v2/league/{game_id}.l.public;out=settings/players;position=ALL;start=0;count=2000;sort=average_pick;search=;out=auction_values,ranks;ranks=o-rank;out=expert_ranks;expert_ranks.rank_type=projected_season_remaining/draft_analysis;cut_types=diamond;slices=last7days?format=json_f
```

* `{game_id}.l.public` is a pseudo public-league query — no league/user context needed.
* `count=2000` returns the **entire** season player pool in one call (no pagination) — confirmed ~1183
  NFL players for game_id 470 (2026 season).
* Each player's `draft_analysis` block has both `average_pick`/`average_round`/`percent_drafted` (ADP) and
  `average_cost` (salary cap $), plus `preseason_*` variants — one call gets both ADP and auction data.
* Numeric fields use `"-"` as a null placeholder for undrafted players — clean with
  `try_cast(nullif(col, '-') as decimal(...))` before casting.
* Implemented in `examples/load_yahoo_adp_public_uc` — writes into the existing `nfl.yh.fact_yahoo_adp`
  table (PK: `player_key`, `game_id`, `snapshot_date`).
* This workaround only covers ADP/salary-cap draft analysis, not the full player pool, league data, or
  weekly stats — those still require the broken OAuth-based `yahoo_fantasy.api.YahooApiClient`.

## Commit Messages

Follow conventional commits:

* `feat:` — new feature or module
* `fix:` — bug fix
* `refactor:` — code restructuring without behavior change
* `chore:` — tooling, CI, deps
* `docs:` — documentation only
* `test:` — adding or fixing tests
