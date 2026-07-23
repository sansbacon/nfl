#!/usr/bin/env python3
"""Load cached Yahoo data and write to Iceberg."""

import argparse
from pathlib import Path
import sys
import os
import json
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).parent / "src"))

from nfl.yahoo_fantasy import PipelineConfig, run_pipeline, build_oauth_session
from nfl.yahoo_fantasy.storage.iceberg import IcebergCatalogConfig, IcebergNamespaceConfig


def _parse_args(default_league_key: str, default_sport: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Yahoo Fantasy data and persist it to Iceberg.",
    )
    parser.add_argument(
        "--league-key",
        default=default_league_key,
        help="Yahoo league key, for example 461.l.717896",
    )
    parser.add_argument(
        "--sport",
        default=default_sport,
        choices=["nfl", "nba"],
        help="Yahoo sport code",
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=None,
        help="Optional start week override",
    )
    parser.add_argument(
        "--end-week",
        type=int,
        default=None,
        help="Optional end week override",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached Yahoo API responses (defaults to fresh fetches).",
    )
    parser.add_argument(
        "--skip-player-points-check",
        action="store_true",
        help="Skip fail-fast check for missing NFL player-level scoring.",
    )
    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=0.4,
        help="Delay between Yahoo API requests to reduce rate limiting.",
    )
    parser.add_argument(
        "--max-request-retries",
        type=int,
        default=5,
        help="Maximum retries for transient Yahoo API failures.",
    )
    parser.add_argument(
        "--backoff-base-seconds",
        type=float,
        default=1.2,
        help="Base seconds used for exponential backoff between retries.",
    )
    parser.add_argument(
        "--player-page-size",
        type=int,
        default=10,
        help="Player pagination size. Smaller values reduce burst pressure.",
    )
    return parser.parse_args()

# Configuration
project_root = Path(__file__).parent
token_path = project_root / ".secrets" / "yahoo_token.json"
credentials_path = project_root / ".secrets" / "credentials.json"
env_path = project_root / ".env"

credentials: dict[str, str] = {}
if credentials_path.exists():
    try:
        raw = json.loads(credentials_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            credentials = raw
    except (OSError, json.JSONDecodeError):
        credentials = {}

env_credentials: dict[str, str] = {}
if env_path.exists():
    loaded = dotenv_values(env_path)
    env_credentials = {str(k): str(v) for k, v in loaded.items() if v is not None}

default_league_key = os.environ.get(
    "YAHOO_LEAGUE_KEY",
    env_credentials.get("YAHOO_LEAGUE_KEY", "461.l.717896"),
).strip()
default_sport = os.environ.get(
    "YAHOO_SPORT",
    env_credentials.get("YAHOO_SPORT", "nfl"),
).strip() or "nfl"

args = _parse_args(default_league_key=default_league_key, default_sport=default_sport)
league_key = args.league_key.strip()
sport = args.sport.strip().lower()

client_id = os.environ.get(
    "YAHOO_CLIENT_ID",
    env_credentials.get("YAHOO_CLIENT_ID", str(credentials.get("client_id", ""))),
).strip()
client_secret = os.environ.get(
    "YAHOO_CLIENT_SECRET",
    env_credentials.get("YAHOO_CLIENT_SECRET", str(credentials.get("client_secret", ""))),
).strip()
redirect_uri = os.environ.get(
    "YAHOO_REDIRECT_URI",
    env_credentials.get("YAHOO_REDIRECT_URI", str(credentials.get("redirect_uri", "http://localhost:8000"))),
).strip()

if not client_id or not client_secret:
    raise RuntimeError(
        "Missing Yahoo OAuth client credentials. "
        "Provide credentials in .env, .secrets/credentials.json, or set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET."
    )

print(f"Loading data for league: {league_key}")
print(f"Sport: {sport}")
print(f"Project root: {project_root}")
print(f"Token path: {token_path}")
if args.start_week is not None or args.end_week is not None:
    print(f"Week window override: start_week={args.start_week}, end_week={args.end_week}")
print(
    "Request tuning: "
    f"interval={args.request_interval_seconds}s, "
    f"retries={args.max_request_retries}, "
    f"backoff={args.backoff_base_seconds}s, "
    f"player_page_size={args.player_page_size}"
)

# Build OAuth session with cached token
oauth = build_oauth_session(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    token_path=token_path,
    auth_code=None,
    open_browser=False,
)

print("Built OAuth session from cached token")

# Configure pipeline for Iceberg persistence
config = PipelineConfig(
    use_cache=args.use_cache,  # Default is fresh API responses to avoid stale payloads
    request_interval_seconds=args.request_interval_seconds,
    max_request_retries=args.max_request_retries,
    backoff_base_seconds=args.backoff_base_seconds,
    player_page_size=args.player_page_size,
    require_nfl_player_points=not args.skip_player_points_check,  # Fail fast unless explicitly disabled
    start_week=args.start_week,
    end_week=args.end_week,
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
        sport=sport,
        oauth_session=oauth,
        config=config,
    )
    print("Pipeline complete")
    print(f"  Iceberg outputs: {len(result.iceberg_outputs)} tables written")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
