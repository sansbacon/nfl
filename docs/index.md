# NFL Package Docs

Welcome to the documentation site for the **nfl** package — a unified Python library for NFL fantasy data ingestion, transformation, and persistence.

## What This Package Provides

The `nfl` package namespace contains four production-oriented libraries:

| Library | Purpose |
|---|---|
| `nfl.yahoo_fantasy` | Yahoo Fantasy ingestion, normalization, and query APIs |
| `nfl.fantasypros_fantasy` | FantasyPros player ADP ingestion and Yahoo crosswalk matching |
| `nfl.nflverse_fantasy` | Broad NFL dataset ingestion from the nflverse project |
| `nfl.entity_standardization` | Cross-source entity matching and canonical player/team resolution |

## Getting Started

1. Read the **[Zensical Guide](ZENSICAL_DOCUMENTATION.md)** for an overview of design principles, module topology, and configuration patterns.
2. Explore the **API Reference** for detailed documentation of each sub-package.
3. Browse the **Practical Examples** to see end-to-end usage in real workflows.

## Site Navigation

- **Zensical Guide** — orientation map of the whole package.
- **API Reference** — module-level documentation for public APIs.
  - [Yahoo Fantasy API](api/yahoo_fantasy.md)
  - [FantasyPros API](api/fantasypros_fantasy.md)
  - [NFLverse API](api/nflverse_fantasy.md)
  - [Entity Standardization API](api/entity_standardization.md)
- **Practical Examples** — annotated, runnable examples for common workflows.
  - [Load Yahoo Data](examples/load_yahoo_data.md)
  - [Load FantasyPros ADP](examples/load_fantasypros_adp.md)
  - [Match Yahoo ↔ FantasyPros Players](examples/match_yahoo_fantasypros.md)
  - [Query Unity Catalog Tables](examples/query_tables.md)
- **Architecture Decision Records** — design rationale and technical decisions.
