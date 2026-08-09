# nfl-databricks

Databricks-specific integrations for the [`nfl`](../nfl/) fantasy football library.

This package provides:

- **Unity Catalog storage adapters** — persist Polars DataFrames as Delta tables or Volume files in Databricks Unity Catalog
- **Lakeflow Connect connector** — a community connector that ingests nflverse data directly into Unity Catalog via Lakeflow pipelines

## Why a Separate Package?

The core `nfl` library is platform-agnostic: it runs on any Python 3.12+ environment
(laptop, CI, any cloud) with zero Databricks or PySpark dependencies. This package
extends it with Databricks-native capabilities that require PySpark and the Databricks
runtime.

## Install

```bash
# Install with all dependencies (requires nfl to be installed or available)
pip install -e ".[dev]"
```

Or from the `nfl` package itself:

```bash
# In the nfl repo — installs nfl + Databricks extensions
pip install -e ".[databricks]"
```

## Usage

### Unity Catalog Storage

```python
import polars as pl
from nfl_databricks.storage import UCTableConfig, persist_to_uc_tables

frames = {
    "player_stats": pl.DataFrame({...}),
    "schedules": pl.DataFrame({...}),
}

results = persist_to_uc_tables(
    frames,
    config=UCTableConfig(catalog="nfl", schema="nv", write_mode="overwrite"),
)
```

### Unity Catalog Volume

```python
from nfl_databricks.storage import UCVolumeConfig, persist_to_uc_volume

results = persist_to_uc_volume(
    frames,
    config=UCVolumeConfig(catalog="nfl", schema="nv", volume="nv_volume"),
)
```

### Lakeflow Connect Connector

The connector in `src/nfl_databricks/connector/` implements the Lakeflow Connect
community connector protocol. Point a Lakeflow pipeline at the `connector/` directory
and configure:

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `seasons` | Yes | — | Comma-separated NFL seasons (e.g. `2022,2023,2024`) |
| `season_type` | No | `REG` | `REG`, `POST`, or `REG_POST` |

See `src/nfl_databricks/connector/README.md` for full deployment instructions.

## Project Layout

```
src/nfl_databricks/
├── __init__.py
├── storage/
│   ├── __init__.py
│   └── unity_catalog.py      # UCTableConfig, persist_to_uc_tables, etc.
└── connector/
    ├── __init__.py
    ├── connector.py           # LakeflowConnect class
    ├── spec.yml               # Connector metadata
    └── README.md              # Deployment instructions

tests/
├── test_storage.py
└── test_connector.py
```

## Testing

```bash
pytest
pytest -m "not integration"   # skip Spark-dependent tests
```

## License

MIT
