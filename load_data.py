#!/usr/bin/env python3
"""Load cached Yahoo data and write to Iceberg."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from nfl.yahoo_fantasy import PipelineConfig, run_pipeline, build_oauth_session
from nfl.yahoo_fantasy.storage.iceberg import IcebergCatalogConfig, IcebergNamespaceConfig

# Configuration
project_root = Path(__file__).parent
token_path = project_root / ".secrets" / "yahoo_token.json"
league_key = "461.l.717896"

print(f"Loading data for league: {league_key}")
print(f"Project root: {project_root}")
print(f"Token path: {token_path}")

# Build OAuth session with cached token
oauth = build_oauth_session(
    client_id="",  # Not needed with cached token
    client_secret="",  # Not needed with cached token
    redirect_uri="http://localhost:8000",
    token_path=token_path,
    auth_code=None,
    open_browser=False,
)

print("✓ Built OAuth session from cached token")

# Configure pipeline for Iceberg persistence
config = PipelineConfig(
    use_cache=False,  # Force fresh API responses to avoid stale roster payloads missing points/stats
    require_nfl_player_points=True,  # Fail fast if player-level scoring data is empty
    storage_target="iceberg",
    iceberg_catalog=IcebergCatalogConfig(
        uri=f"sqlite:///{project_root / 'iceberg_catalog.db'}",
        warehouse=str(project_root / "warehouse"),
    ),
    iceberg_namespaces=IcebergNamespaceConfig(
        nfl="yhnfl",
        nba="ynba",
    ),
    iceberg_dry_run=False,  # Actually write data
)

print("Starting pipeline...")
try:
    result = run_pipeline(
        league_key=league_key,
        sport="nfl",
        oauth_session=oauth,
        config=config,
    )
    print(f"✓ Pipeline complete")
    print(f"  Iceberg outputs: {len(result.iceberg_outputs)} tables written")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
